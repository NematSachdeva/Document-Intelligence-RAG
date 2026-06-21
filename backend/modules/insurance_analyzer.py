"""
Insurance Policy Analyzer - Strict Fact-Based Reports
ONLY analyzes information explicitly present in policy documents.
NO hallucinations. NO assumptions. NO generic explanations.
Compact 4-6 page consultant reports.
"""

from typing import Dict, List, Tuple
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
import os


class InsuranceAnalyzer:
    """Generates ultra-strict, fact-based insurance consultant reports."""
    
    TOKENS_PER_WORD = 1.3
    MAX_CONTEXT_TOKENS = 2500  # Smaller for concise output
    
    def __init__(self, embedding_manager=None):
        self.llm = self._initialize_llm()
        self.embedding_manager = embedding_manager
        
    def _initialize_llm(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not set in environment")
        
        return ChatGroq(
            model="llama-3.1-8b-instant",
            groq_api_key=api_key,
            temperature=0.0  # Absolute zero for factual accuracy
        )
    
    def _estimate_tokens(self, text: str) -> int:
        words = len(text.split())
        return int(words * self.TOKENS_PER_WORD)
    
    def _deduplicate_chunks(self, chunks: List[str]) -> List[str]:
        seen = set()
        result = []
        for chunk in chunks:
            key = chunk[:100].lower()
            if key not in seen:
                seen.add(key)
                result.append(chunk)
        return result
    
    def _retrieve_section_chunks(self, collection_name: str, queries: List[str], top_k: int) -> Tuple[List[str], int]:
        """Retrieve chunks for a specific section from Chroma."""
        all_chunks = []
        
        if not self.embedding_manager:
            return all_chunks, 0
        
        for query in queries:
            try:
                chunks, _, _ = self.embedding_manager.retrieve_similar_chunks(
                    collection_name=collection_name,
                    query=query,
                    top_k=top_k
                )
                all_chunks.extend(chunks)
            except Exception as e:
                print(f"⚠️  Query '{query}': {str(e)}")
        
        all_chunks = self._deduplicate_chunks(all_chunks)
        total_tokens = self._estimate_tokens("\n".join(all_chunks))
        
        return all_chunks, total_tokens
    
    def _generate_section(self, section_name: str, system_prompt: str, context: str, user_query: str) -> str:
        """Generate a single section with strict LLM validation."""
        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"Policy context:\n{context}\n\n{user_query}")
            ]
            
            response = self.llm.invoke(messages)
            output = response.content or ""
            
            # Check for hallucination phrases
            hallucination_phrases = [
                "assuming this",
                "typically",
                "generally",
                "usually",
                "most policies",
                "most insurers",
                "commonly",
                "standard practice"
            ]
            
            output_lower = output.lower()
            for phrase in hallucination_phrases:
                if phrase in output_lower:
                    print(f"⚠️  {section_name}: Detected hallucination phrase '{phrase}'. Returning empty.")
                    return f"*{section_name} not fully documented in policy*"
            
            if not output.strip():
                return f"*{section_name}: Not found in policy document*"
            
            return output
            
        except Exception as e:
            print(f"⚠️  {section_name} generation failed: {str(e)}")
            return f"*{section_name} unavailable due to generation limit*"
    
    def generate_expert_analysis(self, 
                                 document_text: str,
                                 filename: str,
                                 collection_name: str = None) -> str:
        """
        Generate ultra-concise, fact-based insurance consultant report.
        4-6 pages. Zero hallucinations.
        """
        print(f"\n{'='*60}")
        print(f"🚀 GENERATING STRICT FACT-BASED REPORT")
        print(f"Document: {filename}")
        print(f"{'='*60}")
        
        sections = {}
        
        # ===== EXECUTIVE DASHBOARD (5 metrics only) =====
        print("\n📊 Executive Dashboard...")
        dashboard_queries = [
            "policy coverage benefits what is covered",
            "waiting period restrictions limitations",
            "financial limits caps sub-limits",
            "exclusions not covered",
            "claim process restrictions"
        ]
        chunks, _ = self._retrieve_section_chunks(collection_name, dashboard_queries, top_k=2)
        
        dashboard_system = """CRITICAL: Only use facts explicitly stated in the provided policy text.
Generate ONLY this exact format with ratings 1-10:
- Overall Risk Level: [1-10] (10=high risk, 1=low risk)
- Coverage Strength: [1-10]
- Waiting Period Impact: [1-10]
- Financial Restrictions: [1-10]
- Claim Friendliness: [1-10]

RULES:
- If information not found in context: write "Not documented"
- NO explanations after ratings
- NO assumptions
- NO "typically" or "generally"
- Rate based ONLY on what's in provided context"""
        
        dashboard_query = "Rate these 5 metrics based ONLY on the policy document."
        
        sections["Executive Dashboard"] = self._generate_section(
            "Executive Dashboard",
            dashboard_system,
            "\n".join(chunks) if chunks else document_text[:2000],
            dashboard_query
        )
        
        # ===== POLICY SNAPSHOT =====
        print("📋 Policy Snapshot...")
        snapshot_queries = ["policy name company type UIN", "entry age sum insured duration term"]
        chunks, _ = self._retrieve_section_chunks(collection_name, snapshot_queries, top_k=2)
        
        snapshot_system = """Extract ONLY facts stated in policy. Create compact table:
| Field | Value |
|-------|-------|
| Policy Name | [exact name from document] |
| Insurer | [exact company name] |
| Type | [exact type] |
| UIN | [number] |
| Entry Age | [number] |
| Max Age | [number] |
| Sum Insured Options | [list] |
| Duration | [years/months] |

If not explicitly stated: leave blank or write "Not specified"
NO assumptions. NO generic details."""
        
        snapshot_query = "Extract policy snapshot details ONLY from document."
        
        sections["Policy Snapshot"] = self._generate_section(
            "Policy Snapshot",
            snapshot_system,
            "\n".join(chunks) if chunks else document_text[:1500],
            snapshot_query
        )
        
        # ===== COVERAGE ANALYSIS =====
        print("💊 Coverage Analysis...")
        coverage_queries = [
            "inpatient hospitalization coverage limit",
            "ICU critical care limit coverage",
            "outpatient procedures day care",
            "additional benefits covered"
        ]
        chunks, _ = self._retrieve_section_chunks(collection_name, coverage_queries, top_k=3)
        
        coverage_system = """Extract coverages from policy. Create table:
| Coverage | Limit/Scope | Customer Impact |
|----------|-------------|-----------------|
| [name] | [exact limit] | [what it means] |

Customer Impact: 1-2 lines only. FACTS only.
Example: "Covers 30-day ICU max. If hospitalization exceeds 30 days, customer pays balance"

RULES:
- Extract ONLY stated coverages
- Use EXACT limits from document
- If coverage not mentioned: DO NOT INCLUDE
- NO additional benefits you assume exist"""
        
        coverage_query = "List all coverages with exact limits from document."
        
        sections["Coverage Analysis"] = self._generate_section(
            "Coverage Analysis",
            coverage_system,
            "\n".join(chunks) if chunks else document_text[1500:4500],
            coverage_query
        )
        
        # ===== FINANCIAL CAPS & SUB-LIMITS =====
        print("💰 Financial Caps...")
        limits_queries = [
            "room rent daily limit maximum",
            "ICU limit sub-limit capping",
            "disease specific limit cap",
            "surgery limit cataract hernia",
            "ambulance limit daily cash"
        ]
        chunks, _ = self._retrieve_section_chunks(collection_name, limits_queries, top_k=3)
        
        limits_system = """Extract financial caps. Create table:
| Cap/Limit | Amount | Impact |
|-----------|--------|--------|
| [type] | [exact amount] | [customer effect] |

Impact: 1-2 lines explaining financial consequence for customer.

RULES:
- Extract ONLY stated limits
- Use EXACT numbers from document
- If limit not mentioned: DO NOT INVENT
- Impact: how it reduces claim payout, that's ALL"""
        
        limits_query = "Extract all financial caps and limits from policy."
        
        sections["Financial Caps"] = self._generate_section(
            "Financial Caps",
            limits_system,
            "\n".join(chunks) if chunks else document_text[4500:6500],
            limits_query
        )
        
        # ===== WAITING PERIODS =====
        print("⏱️  Waiting Periods...")
        waiting_queries = [
            "waiting period days months",
            "pre-existing disease waiting period",
            "maternity waiting period",
            "specific disease waiting period"
        ]
        chunks, _ = self._retrieve_section_chunks(collection_name, waiting_queries, top_k=3)
        
        waiting_system = """Extract waiting periods. Create table:
| Condition | Duration | Impact |
|-----------|----------|--------|
| [condition] | [X days/months] | [customer effect] |

Impact: 1-2 lines only. Example: "30-day wait means pre-existing conditions not covered first month"

RULES:
- List ONLY stated waiting periods
- Use EXACT durations from document
- If not mentioned: DO NOT LIST
- NO assumptions about standard waiting periods"""
        
        waiting_query = "Extract all waiting periods from policy."
        
        sections["Waiting Periods"] = self._generate_section(
            "Waiting Periods",
            waiting_system,
            "\n".join(chunks) if chunks else document_text[6500:8000],
            waiting_query
        )
        
        # ===== EXCLUSIONS (MANDATORY) =====
        print("🚫 Exclusions...")
        exclusion_queries = [
            "exclusion not covered excluded conditions",
            "disease exclusion treatment exclusion",
            "what is not covered exclusion clause"
        ]
        chunks, _ = self._retrieve_section_chunks(collection_name, exclusion_queries, top_k=3)
        
        exclusion_system = """MANDATORY SECTION. Extract exclusions. Create table:
| Exclusion | Impact |
|-----------|--------|
| [what is excluded] | [why customer should care] |

Impact: 1-2 lines. Example: "LASIK not covered - vision correction denied"

CRITICAL RULES:
- Extract ONLY stated exclusions from document
- If nothing found: "Exclusions not detailed in policy"
- DO NOT list standard insurance exclusions
- DO NOT invent exclusions
- Focus on what customer CANNOT claim"""
        
        exclusion_query = "Extract exclusions from policy."
        
        sections["Exclusions"] = self._generate_section(
            "Exclusions",
            exclusion_system,
            "\n".join(chunks) if chunks else document_text[8000:9500],
            exclusion_query
        )
        
        if "*unavailable*" in sections["Exclusions"].lower():
            sections["Exclusions"] = "Exclusions could not be generated due to model rate limits. Please check policy document directly."
        
        # ===== CLAIM RESTRICTIONS =====
        print("📝 Claim Restrictions...")
        restriction_queries = [
            "claim restriction condition limit requirement",
            "claim filing deadline documentation required",
            "network hospital requirement reimbursement",
            "claim process restriction"
        ]
        chunks, _ = self._retrieve_section_chunks(collection_name, restriction_queries, top_k=2)
        
        restriction_system = """Extract claim restrictions. Create table:
| Restriction | Effect |
|-------------|--------|
| [restriction] | [customer impact] |

Effect: 1-2 lines. Example: "Claim must be filed within 30 days or may be rejected"

RULES:
- Extract ONLY stated restrictions
- If not mentioned: DO NOT LIST
- NO generic claim process steps
- NO assumptions about standard procedures"""
        
        restriction_query = "Extract claim restrictions from policy."
        
        sections["Claim Restrictions"] = self._generate_section(
            "Claim Restrictions",
            restriction_system,
            "\n".join(chunks) if chunks else document_text[9500:10800],
            restriction_query
        )
        
        # ===== KEY CLAUSES (ONLY 4 max, 2 lines each) =====
        print("📜 Key Clauses...")
        clause_queries = [
            "renewal grace period cancellation free look",
            "portability migration policy change",
            "premium payment term modification"
        ]
        chunks, _ = self._retrieve_section_chunks(collection_name, clause_queries, top_k=2)
        
        clause_system = """Extract ONLY 4 key clauses. Maximum 2 lines each.
Format:
- **Renewal**: [policy] (2 lines max)
- **Cancellation**: [policy] (2 lines max)
- **Grace Period**: [policy] (2 lines max)
- **Portability**: [policy] (2 lines max)

Example line: "Policy renews automatically. Can cancel anytime with 30-day notice"

RULES:
- Extract ONLY from document
- NO generic definitions
- NO "what it means" explanations
- If clause not found: skip it
- 2 lines MAXIMUM per clause"""
        
        clause_query = "Extract key clauses from policy - 4 max, 2 lines each."
        
        sections["Key Clauses"] = self._generate_section(
            "Key Clauses",
            clause_system,
            "\n".join(chunks) if chunks else document_text[10800:11800],
            clause_query
        )
        
        # ===== FINAL RECOMMENDATION (250 words max) =====
        print("✅ Recommendation...")
        rec_queries = [
            "policy benefits coverage type target customer",
            "policy limitations restrictions who should avoid",
            "policy strengths weaknesses advantages disadvantages"
        ]
        chunks, _ = self._retrieve_section_chunks(collection_name, rec_queries, top_k=2)
        
        rec_system = """Create FINAL RECOMMENDATION. Maximum 250 words total.

Format:
**Suitable For:**
- [customer type] - [reason from policy]

**Not Suitable For:**
- [customer type] - [reason from policy]

**Key Pros:**
- [strength from policy]

**Key Cons:**
- [limitation from policy]

RULES:
- Use ONLY policy facts
- NO assumptions
- NO "typically" or "usually"
- NO generic insurance advice
- Be honest about tradeoffs
- MAX 250 words total"""
        
        rec_query = "Create recommendation based ONLY on policy terms."
        
        sections["Final Recommendation"] = self._generate_section(
            "Final Recommendation",
            rec_system,
            "\n".join(chunks) if chunks else document_text[11800:13500],
            rec_query
        )
        
        # ===== BUILD REPORT =====
        print(f"\n{'='*60}")
        print(f"📄 Building compact 4-6 page report...")
        print(f"{'='*60}\n")
        
        final_report = f"""# Insurance Policy Analysis Report

**Document:** {filename}  
**Generated:** {__import__('datetime').datetime.now().strftime('%B %d, %Y')}

---

## Executive Dashboard

{sections.get('Executive Dashboard', '*Dashboard unavailable*')}

---

## Policy Snapshot

{sections.get('Policy Snapshot', '*Snapshot unavailable*')}

---

## Coverage Analysis

{sections.get('Coverage Analysis', '*Coverage unavailable*')}

---

## Financial Caps & Sub-Limits

{sections.get('Financial Caps', '*Financial information unavailable*')}

---

## Waiting Periods

{sections.get('Waiting Periods', '*No waiting periods documented*')}

---

## Exclusions

{sections.get('Exclusions', '*Exclusions not documented*')}

---

## Claim Restrictions

{sections.get('Claim Restrictions', '*Restrictions not documented*')}

---

## Key Clauses

{sections.get('Key Clauses', '*Clauses not documented*')}

---

## Final Recommendation

{sections.get('Final Recommendation', '*Recommendation unavailable*')}

---

*Based solely on policy document. For complete terms, refer to original policy.*
"""
        
        print("✅ Report completed!")
        return final_report
