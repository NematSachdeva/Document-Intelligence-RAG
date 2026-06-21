"""
FastAPI Application
Main entry point for the PDF Document Assistant.
Orchestrates PDF processing, embedding generation, and QA.
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Dict, List
import os
import shutil
import uuid
import io
from dotenv import load_dotenv

# Import modules
from modules.parser import get_page_wise_text
from modules.chunker import chunk_text, get_chunks_with_metadata
from modules.embeddings import EmbeddingManager
from modules.qa import QAEngine
from modules.summarizer import Summarizer
from modules.insurance_analyzer import InsuranceAnalyzer
from modules.pdf_reporter import ProfessionalPDFReporter

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="PDF Document Assistant",
    description="AI-powered PDF analysis with semantic search and QA",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", 50000000))

# Create directories
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Initialize managers
embedding_manager = EmbeddingManager()
qa_engine = QAEngine()
summarizer = Summarizer()
insurance_analyzer = InsuranceAnalyzer(embedding_manager=embedding_manager)
# Don't create a global pdf_reporter instance - create new one per request

# Store document metadata in memory (in production, use database)
documents_metadata = {}
# Track the active document (single document mode for insurance policies)
active_document_id = None


# Helper Functions

def parse_analysis_markdown(markdown_text: str) -> Dict:
    """
    Parse markdown report into sections for frontend display.
    Returns a dictionary with section titles as keys and content as values.
    """
    sections = {
        "dashboard": "",
        "snapshot": "",
        "coverage": "",
        "financial_limits": "",
        "waiting_periods": "",
        "exclusions": "",
        "claim_restrictions": "",
        "important_clauses": "",
        "recommendation": ""
    }
    
    # Map section headers to keys - MUST MATCH what insurance_analyzer.py generates
    section_map = {
        "## Executive Dashboard": "dashboard",
        "## Policy Snapshot": "snapshot",
        "## Coverage Analysis": "coverage",
        "## Financial Caps & Sub-Limits": "financial_limits",
        "## Waiting Periods": "waiting_periods",
        "## Exclusions": "exclusions",  # Fixed: was "## Exclusions & Risks"
        "## Claim Restrictions": "claim_restrictions",
        "## Key Clauses": "important_clauses",  # Fixed: was "## Important Clauses"
        "## Final Recommendation": "recommendation"
    }
    
    current_section = None
    current_content = []
    lines = markdown_text.split('\n')
    
    for i, line in enumerate(lines):
        # Check if this line starts a new section
        section_found = False
        for heading, key in section_map.items():
            if line.strip() == heading.strip():
                # Save previous section
                if current_section and current_content:
                    sections[current_section] = '\n'.join(current_content).strip()
                current_section = key
                current_content = []
                section_found = True
                break
        
        # If not a new section header, accumulate content
        if not section_found and current_section is not None:
            current_content.append(line)
    
    # Save last section
    if current_section and current_content:
        sections[current_section] = '\n'.join(current_content).strip()
    
    # Filter out empty sections
    filtered = {k: v for k, v in sections.items() if v.strip()}
    print(f"[Parse] Parsed sections: {list(filtered.keys())}")
    return filtered


# Request/Response Models
class QuestionRequest(BaseModel):
    document_id: str
    question: str


class AnswerResponse(BaseModel):
    answer: str
    citations: List[Dict]
    success: bool


class SummaryResponse(BaseModel):
    summary: str
    key_points: List[str]
    main_topics: List[str]
    success: bool


class UploadResponse(BaseModel):
    document_id: str
    filename: str
    pages: int
    chunks: int
    summary: Dict
    analysis: Dict
    success: bool


class AnalysisRequest(BaseModel):
    document_id: str


class AnalysisResponse(BaseModel):
    filename: str
    analysis: Dict
    success: bool


# API Endpoints

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "PDF Document Assistant API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

@app.post("/upload", response_model=UploadResponse)
async def upload_pdf(file: UploadFile = File(...)):
    """
    Upload and process a PDF document.
    For insurance policies: only one document can be active at a time.
    When a new PDF is uploaded, the previous document is deleted.
    
    1. Delete previous active document if exists
    2. Save PDF
    3. Extract text with OCR fallback
    4. Create chunks (optimized to reduce embeddings count)
    5. Generate embeddings
    6. Generate summary
    """
    global active_document_id
    
    try:
        # Validate file
        if not file.filename.endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
        if file.size and file.size > MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail="File too large")
        
        # Delete previous active document and its Chroma collection
        if active_document_id and active_document_id in documents_metadata:
            print(f"Deleting previous active document: {active_document_id}")
            try:
                collection_name = documents_metadata[active_document_id]["collection_name"]
                embedding_manager.delete_collection(collection_name)
                
                # Delete file
                file_path = os.path.join(UPLOAD_DIR, f"{active_document_id}.pdf")
                if os.path.exists(file_path):
                    os.remove(file_path)
                
                del documents_metadata[active_document_id]
            except Exception as e:
                print(f"Warning: Could not delete previous document: {str(e)}")
        
        # Generate document ID (unique for each PDF)
        document_id = f"{file.filename.replace('.pdf', '').replace(' ', '_')}_{uuid.uuid4().hex[:8]}"
        file_path = os.path.join(UPLOAD_DIR, f"{document_id}.pdf")
        
        # Create unique collection name for this document
        collection_name = f"doc_{document_id}"
        
        # Save file
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        print(f"Processing document: {document_id}")
        
        # Extract text from PDF
        page_texts = get_page_wise_text(file_path)
        num_pages = len(page_texts)
        
        # Create chunks with larger size and smaller overlap to reduce embeddings count
        # This keeps under Chroma Cloud free tier quota (300 records)
        chunks = chunk_text(page_texts, chunk_size=1000, overlap=50)
        texts, metadatas, ids = get_chunks_with_metadata(chunks)
        
        print(f"Creating {len(chunks)} embeddings for document")
        
        # Store embeddings in Chroma Cloud
        embedding_manager.store_embeddings(
            collection_name=collection_name,
            texts=texts,
            metadatas=metadatas,
            ids=ids
        )
        
        # Generate summary
        full_text = " ".join(page_texts.values())
        summary_result = summarizer.generate_summary(full_text)
        
        # Generate insurance analysis
        print(f"Generating insurance analysis for document")
        analysis_markdown = insurance_analyzer.generate_expert_analysis(
            document_text=full_text,
            filename=file.filename,
            collection_name=collection_name
        )
        
        # Parse analysis into sections for frontend display
        analysis_sections = parse_analysis_markdown(analysis_markdown)
        
        # Store metadata and set as active document
        documents_metadata[document_id] = {
            "filename": file.filename,
            "pages": num_pages,
            "chunks": len(chunks),
            "summary": summary_result,
            "collection_name": collection_name,
            "full_text": full_text,
            "analysis_markdown": analysis_markdown,
            "analysis_sections": analysis_sections
        }
        
        active_document_id = document_id
        
        return UploadResponse(
            document_id=document_id,
            filename=file.filename,
            pages=num_pages,
            chunks=len(chunks),
            summary=summary_result,
            analysis=analysis_sections,
            success=True
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")


@app.post("/ask", response_model=AnswerResponse)
async def ask_question(request: QuestionRequest):
    """
    Ask a question about an uploaded document.
    
    1. Retrieve relevant chunks using semantic search from document's collection
    2. Build context
    3. Generate answer with LLM
    4. Return answer with citations
    """
    try:
        document_id = request.document_id
        question = request.question
        
        # Validate document exists
        if document_id not in documents_metadata:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Get the collection name for this document
        collection_name = documents_metadata[document_id]["collection_name"]
        
        # Retrieve similar chunks from this document's collection
        chunks, metadatas, distances = embedding_manager.retrieve_similar_chunks(
            collection_name=collection_name,
            query=question,
            top_k=5
        )
        
        if not chunks:
            return AnswerResponse(
                answer="No relevant information found in the document.",
                citations=[],
                success=False
            )
        
        # Generate answer
        result = qa_engine.answer_question(question, chunks, metadatas)
        
        return AnswerResponse(
            answer=result["answer"],
            citations=result["citations"],
            success=result["success"]
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error answering question: {str(e)}")


@app.get("/summary/{document_id}", response_model=SummaryResponse)
async def get_summary(document_id: str):
    """Get the stored summary for a document."""
    try:
        if document_id not in documents_metadata:
            raise HTTPException(status_code=404, detail="Document not found")
        
        summary_data = documents_metadata[document_id]["summary"]
        
        return SummaryResponse(
            summary=summary_data.get("summary", ""),
            key_points=summary_data.get("key_points", []),
            main_topics=summary_data.get("main_topics", []),
            success=summary_data.get("success", False)
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving summary: {str(e)}")


@app.get("/documents")
async def list_documents():
    """List all uploaded documents with metadata."""
    return {
        "documents": [
            {
                "document_id": doc_id,
                "filename": metadata["filename"],
                "pages": metadata["pages"],
                "chunks": metadata["chunks"]
            }
            for doc_id, metadata in documents_metadata.items()
        ]
    }


@app.delete("/documents/{document_id}")
async def delete_document(document_id: str):
    """Delete a document and its embeddings from its collection."""
    try:
        if document_id not in documents_metadata:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Get the collection name for this document
        collection_name = documents_metadata[document_id]["collection_name"]
        
        # Delete the collection from ChromaDB
        embedding_manager.delete_collection(collection_name)
        
        # Delete from metadata
        del documents_metadata[document_id]
        
        # Delete file
        file_path = os.path.join(UPLOAD_DIR, f"{document_id}.pdf")
        if os.path.exists(file_path):
            os.remove(file_path)
        
        return {"success": True, "message": "Document deleted"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting document: {str(e)}")


@app.post("/analysis")
async def get_analysis_pdf(request: AnalysisRequest):
    """
    Generate professional PDF report using ProfessionalPDFReporter.
    Uses cached analysis sections from upload, does not regenerate.
    Converts structured sections to professional PDF with tables, styling, and proper formatting.
    """
    try:
        document_id = request.document_id
        
        # Validate document exists
        if document_id not in documents_metadata:
            raise HTTPException(status_code=404, detail="Document not found")
        
        metadata = documents_metadata[document_id]
        
        if "analysis_sections" not in metadata:
            raise HTTPException(status_code=404, detail="No analysis available. Please upload a document first.")
        
        # Get analysis sections and metadata
        analysis_sections = metadata["analysis_sections"]
        filename = metadata["filename"]
        
        # Extract policy name and company from filename and analysis
        policy_name = filename.replace('.pdf', '').strip()
        company_name = "Insurance Company"  # Default; could be extracted from dashboard
        
        # Create PDF in memory with fresh reporter instance
        pdf_filename = f"/tmp/{document_id}_analysis.pdf"
        
        # Create a fresh reporter instance for each PDF generation
        pdf_reporter = ProfessionalPDFReporter()
        pdf_reporter.generate_pdf(
            filename=pdf_filename,
            policy_name=policy_name,
            company_name=company_name,
            analysis_sections=analysis_sections
        )
        
        # Read PDF and return
        with open(pdf_filename, 'rb') as f:
            pdf_bytes = f.read()
        
        # Clean up temp file
        if os.path.exists(pdf_filename):
            os.remove(pdf_filename)
        
        # Return PDF file
        clean_filename = filename.replace('.pdf', '')
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={clean_filename}_Analysis_Report.pdf"}
        )
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in analysis endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating PDF: {str(e)}")


@app.get("/analysis/{document_id}")
async def get_analysis(document_id: str):
    """Get the stored analysis markdown for a document."""
    try:
        if document_id not in documents_metadata:
            raise HTTPException(status_code=404, detail="Document not found")
        
        metadata = documents_metadata[document_id]
        
        if "analysis_markdown" not in metadata:
            raise HTTPException(status_code=404, detail="No analysis available. Please run analyze endpoint first.")
        
        return {
            "document_id": document_id,
            "filename": metadata["filename"],
            "analysis": metadata["analysis_markdown"],
            "success": True
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving analysis: {str(e)}")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "llm_provider": "groq",
        "documents_loaded": len(documents_metadata)
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
