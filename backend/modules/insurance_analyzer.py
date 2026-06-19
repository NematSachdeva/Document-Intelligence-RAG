"""
Insurance Policy Analyzer Module
Extracts key insurance policy information and generates analysis reports.
"""

from typing import Dict, List
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
import os
import json


class InsuranceAnalyzer:
    """Analyzes insurance policy documents and extracts key information."""
    
    def __init__(self):
        """Initialize analyzer with Groq LLM."""
        self.llm = self._initialize_llm()
        
    def _initialize_llm(self):
        """Initialize the Groq LLM."""
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not set in environment")
        
        return ChatGroq(
            model="llama-3.1-8b-instant",
            groq_api_key=api_key,
            temperature=0.1  # Lower temperature for accuracy
        )
    
    def extract_policy_information(self, document_text: str) -> Dict:
        """
        Extract all insurance policy fields from document.
        
        Args:
            document_text: Full document text
            
        Returns:
            Dict with all extracted insurance policy information
        """
        system_prompt = """You are an expert insurance policy analyst. Extract the following information from the insurance policy document.
        
IMPORTANT INSTRUCTIONS:
1. Extract EXACT values from the document, do not infer or assume
2. If a field is not mentioned, write "Not specified in document"
3. For each field, include the page number if available (e.g., "Page 2")
4. Write all amounts in plain language (e.g., "Rs. 100,000" or "$50,000")
5. Be precise and factual
6. Return response as JSON format with the fields below

Extract these 13 key insurance policy fields:
1. Policy Overview - Brief description of the policy
2. Coverage Amount - Total coverage/sum insured
3. Premium Amount - Annual or monthly premium
4. Policy Duration - How long the policy is valid
5. Covered Items - What is covered under the policy
6. Exclusions - What is NOT covered
7. Waiting Periods - Any waiting periods before coverage starts
8. Deductibles - Amount the policyholder must pay
9. Co-pay Clauses - Shared payment terms
10. Renewal Clauses - How to renew the policy
11. Cancellation Clauses - How to cancel and conditions
12. Major Risks - Main risks covered
13. Overall Assessment - Your professional assessment of the policy (understandability, clarity, value)

Return JSON with these exact keys."""
        
        user_message = f"""Please analyze this insurance policy document and extract all required information.

DOCUMENT TEXT:
{document_text[:5000]}

Return the information in this JSON format:
{{
  "policy_overview": "...",
  "coverage_amount": "...",
  "premium_amount": "...",
  "policy_duration": "...",
  "covered_items": "...",
  "exclusions": "...",
  "waiting_periods": "...",
  "deductibles": "...",
  "copay_clauses": "...",
  "renewal_clauses": "...",
  "cancellation_clauses": "...",
  "major_risks": "...",
  "overall_assessment": "..."
}}"""
        
        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_message)
            ]
            
            response = self.llm.invoke(messages)
            response_text = response.content
            
            # Parse JSON from response
            try:
                # Try to extract JSON from response
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                if json_start != -1 and json_end > json_start:
                    json_str = response_text[json_start:json_end]
                    analysis = json.loads(json_str)
                else:
                    # If no JSON found, create structured response
                    analysis = self._parse_text_response(response_text)
            except json.JSONDecodeError:
                analysis = self._parse_text_response(response_text)
            
            return analysis
            
        except Exception as e:
            return {
                "error": f"Failed to analyze policy: {str(e)}",
                "policy_overview": "Error in analysis",
                "coverage_amount": "Error",
                "premium_amount": "Error",
                "policy_duration": "Error",
                "covered_items": "Error",
                "exclusions": "Error",
                "waiting_periods": "Error",
                "deductibles": "Error",
                "copay_clauses": "Error",
                "renewal_clauses": "Error",
                "cancellation_clauses": "Error",
                "major_risks": "Error",
                "overall_assessment": "Error"
            }
    
    def _parse_text_response(self, text: str) -> Dict:
        """Parse text response into structured format."""
        return {
            "policy_overview": "See analysis",
            "coverage_amount": "See analysis",
            "premium_amount": "See analysis",
            "policy_duration": "See analysis",
            "covered_items": "See analysis",
            "exclusions": "See analysis",
            "waiting_periods": "See analysis",
            "deductibles": "See analysis",
            "copay_clauses": "See analysis",
            "renewal_clauses": "See analysis",
            "cancellation_clauses": "See analysis",
            "major_risks": "See analysis",
            "overall_assessment": text[:500]
        }
