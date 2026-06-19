"""
Insurance Policy Analyzer Module - Enhanced Version
Generates professional insurance consultant-quality reports with section-specific RAG retrieval.
Single LLM call approach - no JSON parsing from LLM output.
"""

from typing import Dict, List
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
import os


class InsuranceAnalyzer:
    """Analyzes insurance policies using section-specific RAG + markdown generation."""
    
    def __init__(self, embedding_manager=None):
        """Initialize analyzer with Groq LLM and embedding manager for RAG."""
        self.llm = self._initialize_llm()
        self.embedding_manager = embedding_manager
        
    def _initialize_llm(self):
        """Initialize the Groq LLM."""
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not set in environment")
        
        return ChatGroq(
            model="llama-3.1-8b-instant",
            groq_api_key=api_key,
            temperature=0.2
        )
    
    def _retrieve_section_chunks(self, collection_name: str, section_queries: Dict[str, List[str]], top_k: int = 5) -> Dict[str, str]:
        """
        Retrieve section-specific relevant chunks from Chroma.
        
        Args:
            collection_name: Chroma collection name
            section_queries: Dict mapping section names to query lists
            top_k: Number of top results per query
            
        Returns:
            Dict mapping section names to merged context
        """
        section_context = {}
        
        if not self.embedding_manager:
            return section_context
        
        try:
            for section_name, queries in section_queries.items():
                all_chunks = []
                
                for query in queries:
                    try:
                        chunks, metadatas, distances = self.embedding_manager.retrieve_similar_chunks(
                            collection_name=collection_name,
                            query=query,
                            top_k=top_k
                        )
                        
                        if chunks:
                            all_chunks.extend(chunks)
                    except Exception as e:
                        print(f"⚠️ Error retrieving {section_name}: {str(e)}")
                        continue
                
                # Deduplicate and merge chunks
                if all_chunks:
                    section_context[section_name] = "\n".join(list(dict.fromkeys(all_chunks))[:top_k*2])
                else:
                    section_context[section_name] = ""
        
        except Exception as e:
            print(f"⚠️ Error in section retrieval: {str(e)}")
        
        return section_context
    
    def generate_expert_analysis(self, 
                                 document_text: str,
                                 filename: str,
                                 collection_name: str = None) -> str:
        """
        Generate professional insurance consultant-quality report as markdown.
        
        Uses section-specific RAG retrieval, then generates markdown in ONE LLM call.
        
        Args:
            document_text: Full policy document text
            filename: Original PDF filename
            collection_name: Optional Chroma collection for RAG
            
        Returns:
            Markdown formatted consultant-quality report as string
        """
        print("🔍 Starting section-specific RAG retrieval...")
        
        # Section-specific retrieval queries
        section_queries = {
            "Policy Snapshot": [
                "policy name insurance company UIN policy type",
                "entry age family coverage eligibility",
                "policy duration term period"
            ],
            "Coverage Details": [
                "inpatient hospitalization ICU coverage",
                "day care surgery procedures ambulance",
                "domiciliary home treatment health checkup",
                "organ donor cover modern treatment",
                "coverage limits amount insured"
            ],
            "Financial Limits": [
                "room rent limit capping",
                "ICU limit daily limits",
                "cataract surgery limits caps",
                "disease specific limits restrictions",
                "ambulance limit daily cash limit",
                "sub-limit maximum limit"
            ],
            "Waiting Periods": [
                "waiting period pre-existing diseases",
                "cataract hernia joint replacement",
                "maternity waiting period disease waiting",
                "exclusion period continuation"
            ],
            "Exclusions": [
                "exclusions not covered excluded conditions",
                "disease exclusions specific exclusions",
                "treatment not covered exclusion clause"
            ],
            "Claim Restrictions": [
                "claim restriction room rent restriction",
                "network hospital restriction reimbursement limit",
                "claim filing deadline documentation requirement",
                "proportionate deduction claim reduction"
            ],
            "Important Clauses": [
                "renewal clause cancellation clause portability",
                "migration free look period premium loading",
                "grace period change sum insured",
                "claim conditions claim settlement"
            ]
        }
        
        # Retrieve section-specific context
        section_contexts = {}
        if self.embedding_manager and collection_name:
            section_contexts = self._retrieve_section_chunks(collection_name, section_queries, top_k=5)
        
        # Build section context string
        context_sections = []
        for section, content in section_contexts.items():
            if content:
                context_sections.append(f"## {section}\n{content}")
        
        merged_context = "\n\n".join(context_sections) if context_sections else document_text[:8000]
        
        print("📝 Generating professional consultant report...")
        
        system_prompt = """You are a Senior Insurance Consultant with 20+ years of experience analyzing health, life, motor, travel and commercial insurance policies.

Your task is to generate a PROFESSIONAL INSURANCE ANALYSIS REPORT that helps customers make informed decisions.

CRITICAL REQUIREMENTS:
1. Write like an insurance advisor, NOT a document summarizer
2. Convert legal jargon to plain English
3. FOCUS on customer impact, not policy wording
4. HIGHLIGHT: limits, caps, restrictions, waiting periods, risks
5. Use markdown formatting professionally
6. Include page references where available
7. Flag risks with ⚠️, benefits with ✅, restrictions with 🚫
8. Provide financial analysis where possible
9. Generate tables for comparative data
10. NEVER be generic - extract actual numbers and specific terms

MANDATORY SECTIONS (in this order):
# POLICY SNAPSHOT
- Policy name, company, type, UIN
- Duration, entry age, sum insured options
- Family eligibility

# EXECUTIVE SUMMARY
Explain in 200 words max:
- What this policy is
- Who it's designed for
- Main strengths
- Main limitations

# COVERAGE ANALYSIS
For each coverage: name, what's covered, financial limit, page ref

# FINANCIAL CAPS AND SUB-LIMITS
Create a table: Benefit | Limit | Customer Impact | Page
Include room rent, ICU, cataract, surgery, disease-specific limits

# WAITING PERIOD ANALYSIS
Table: Condition | Duration | Risk Level | Page
Then explain impact on customers in plain English

# EXCLUSIONS ANALYSIS
Table: Exclusion | Impact | Risk Level | Page
Focus on exclusions affecting claims

# CLAIM RESTRICTIONS
Identify and explain:
- Room rent restrictions
- Proportionate deduction clauses
- Network restrictions
- Reimbursement limits
- Claim filing deadlines
- Documentation requirements

# IMPORTANT CLAUSES
Explain: Renewal, Cancellation, Portability, Migration, Free Look, Premium Loading, Change in SI, Grace Period

# CUSTOMER RED FLAGS
For each: Severity (LOW/MEDIUM/HIGH), Reason, Customer Impact

# BEST FEATURES
List top 10 strongest features with benefits

# INSURANCE SCORECARD
Coverage: X/10 | Claim Friendly: X/10 | Flexibility: X/10 | Transparency: X/10 | Waiting Periods: X/10 | Overall: X/10
Include reasoning

# FINAL RECOMMENDATION
Suitable For | Not Suitable For | Major Advantages | Major Disadvantages (max 300 words)

OUTPUT QUALITY:
- Use tables whenever possible
- Include actual numbers, not generic descriptions
- Highlight financial caps clearly
- Explain why each restriction matters
- Make it decision-friendly"""
        
        user_message = f"""Generate a professional insurance analysis report for: {filename}

POLICY INFORMATION FROM DOCUMENT:
{merged_context}

Create a comprehensive, consultant-quality report that helps customers understand:
- Exactly what is covered and the limits
- What waiting periods apply and their impact
- Which exclusions matter most
- Financial restrictions that affect claims
- Whether this policy is right for them

Be specific. Include numbers, amounts, and durations from the document.
If something is not in the document, state "Not specified in the policy document"."""
        
        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_message)
            ]
            
            response = self.llm.invoke(messages)
            markdown_report = response.content
            
            print("✨ Professional report generated successfully!")
            return markdown_report
            
        except Exception as e:
            print(f"❌ Error generating report: {str(e)}")
            error_report = f"""# Error Generating Insurance Analysis Report

Failed to generate policy analysis: {str(e)}

Please try again or contact support if the issue persists."""
            return error_report
