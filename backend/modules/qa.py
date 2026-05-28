"""
Question Answering Module
Retrieves relevant chunks and generates answers using LLM (Groq).
"""

from typing import Dict, List, Tuple
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
import os


class QAEngine:
    """Handles question answering with context retrieval using Groq."""
    
    def __init__(self):
        """Initialize QA engine with Groq LLM."""
        self.llm = None
        self._initialize_llm()
    
    def _initialize_llm(self):
        """Initialize the Groq LLM."""
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key or api_key == "your_groq_api_key_here":
            print("⚠️  GROQ_API_KEY not configured. QA will not work until configured.")
            return
        
        try:
            self.llm = ChatGroq(
                model="llama-3.1-8b-instant",
                groq_api_key=api_key,
                temperature=0.3
            )
        except Exception as e:
            print(f"⚠️  Failed to initialize Groq: {e}")
    
    def build_context(
        self,
        chunks: List[str],
        metadatas: List[Dict]
    ) -> Tuple[str, List[Dict]]:
        """
        Build context string from retrieved chunks with citations.
        
        Args:
            chunks: List of retrieved text chunks
            metadatas: List of metadata for chunks
        
        Returns:
            Tuple of (context_string, citations)
        """
        context_parts = []
        citations = []
        
        for i, (chunk, metadata) in enumerate(zip(chunks, metadatas)):
            page_num = metadata.get("page_number", "Unknown")
            context_parts.append(f"[Source {i+1} - Page {page_num}]:\n{chunk}\n")
            citations.append({
                "source_id": i + 1,
                "page_number": page_num,
                "chunk_id": metadata.get("chunk_id", "")
            })
        
        context = "\n".join(context_parts)
        return context, citations
    
    def generate_answer(
        self,
        question: str,
        context: str,
        citations: List[Dict]
    ) -> Dict:
        """
        Generate answer using Groq LLM with grounded context.
        
        Args:
            question: User's question
            context: Retrieved context from chunks
            citations: Citation metadata
        
        Returns:
            Dict with answer and citations
        """
        system_prompt = """You are a helpful assistant that answers questions based ONLY on the provided context.
        
IMPORTANT RULES:
1. Answer ONLY using information from the provided context
2. If the answer is not found in the context, respond with: "Information not available in the document."
3. Be concise and accurate
4. When referencing information, mention the source number (e.g., "According to Source 1...")
5. Do not make up or assume information not in the context"""
        
        user_message = f"""Context from document:
{context}

Question: {question}

Please answer the question based only on the provided context."""
        
        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_message)
            ]
            
            response = self.llm.invoke(messages)
            answer = response.content
            
            return {
                "answer": answer,
                "citations": citations,
                "success": True
            }
        except Exception as e:
            return {
                "answer": f"Error generating answer: {str(e)}",
                "citations": [],
                "success": False
            }
    
    def answer_question(
        self,
        question: str,
        chunks: List[str],
        metadatas: List[Dict]
    ) -> Dict:
        """
        Complete QA pipeline: build context and generate answer.
        
        Args:
            question: User's question
            chunks: Retrieved text chunks
            metadatas: Metadata for chunks
        
        Returns:
            Dict with answer and citations
        """
        context, citations = self.build_context(chunks, metadatas)
        result = self.generate_answer(question, context, citations)
        return result
