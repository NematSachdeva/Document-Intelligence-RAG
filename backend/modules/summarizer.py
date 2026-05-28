"""
Summarizer Module
Generates concise summaries of uploaded documents using Groq.
"""

from typing import Dict, List
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
import os


class Summarizer:
    """Generates document summaries using Groq LLM."""
    
    def __init__(self):
        """Initialize summarizer with Groq LLM."""
        self.llm = self._initialize_llm()
    
    def _initialize_llm(self):
        """Initialize the Groq LLM."""
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not set in environment")
        
        return ChatGroq(
            model="llama-3.1-8b-instant",
            groq_api_key=api_key,
            temperature=0.3
        )
    
    def generate_summary(self, text: str, max_length: int = 500) -> Dict:
        """
        Generate a concise summary of the document.
        
        Args:
            text: Full document text
            max_length: Maximum length of summary in characters
        
        Returns:
            Dict with summary and key points
        """
        system_prompt = """You are an expert document summarizer. 
        
Your task is to:
1. Create a concise summary (2-3 sentences)
2. Extract 3-5 key points
3. Identify main topics

Format your response as:
SUMMARY: [concise summary here]

KEY POINTS:
- [point 1]
- [point 2]
- [point 3]

MAIN TOPICS: [comma-separated topics]"""
        
        user_message = f"""Please summarize this document:

{text[:3000]}"""  # Limit to first 3000 chars for efficiency
        
        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_message)
            ]
            
            response = self.llm.invoke(messages)
            content = response.content
            
            # Parse response
            summary_dict = self._parse_summary_response(content)
            summary_dict["success"] = True
            
            return summary_dict
        except Exception as e:
            return {
                "summary": f"Error generating summary: {str(e)}",
                "key_points": [],
                "main_topics": [],
                "success": False
            }
    
    def _parse_summary_response(self, response: str) -> Dict:
        """Parse LLM response into structured summary."""
        result = {
            "summary": "",
            "key_points": [],
            "main_topics": []
        }
        
        try:
            # Extract summary
            if "SUMMARY:" in response:
                summary_part = response.split("SUMMARY:")[1].split("KEY POINTS:")[0].strip()
                result["summary"] = summary_part
            
            # Extract key points
            if "KEY POINTS:" in response:
                key_points_part = response.split("KEY POINTS:")[1].split("MAIN TOPICS:")[0].strip()
                points = [p.strip().lstrip("- ") for p in key_points_part.split("\n") if p.strip()]
                result["key_points"] = points
            
            # Extract main topics
            if "MAIN TOPICS:" in response:
                topics_part = response.split("MAIN TOPICS:")[1].strip()
                topics = [t.strip() for t in topics_part.split(",")]
                result["main_topics"] = topics
        except Exception as e:
            print(f"Error parsing summary: {e}")
            result["summary"] = response
        
        return result
