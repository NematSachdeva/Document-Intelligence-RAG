"""
FastAPI Application
Main entry point for the PDF Document Assistant.
Orchestrates PDF processing, embedding generation, and QA.
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
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
from modules.report_generator import ReportGenerator

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
insurance_analyzer = InsuranceAnalyzer()
report_generator = ReportGenerator()

# Store document metadata in memory (in production, use database)
documents_metadata = {}
# Track the active document (single document mode for insurance policies)
active_document_id = None


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
    4. Create chunks
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
        
        # Create chunks
        chunks = chunk_text(page_texts, chunk_size=500, overlap=100)
        texts, metadatas, ids = get_chunks_with_metadata(chunks)
        
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
        
        # Store metadata and set as active document
        documents_metadata[document_id] = {
            "filename": file.filename,
            "pages": num_pages,
            "chunks": len(chunks),
            "summary": summary_result,
            "collection_name": collection_name,
            "full_text": full_text
        }
        
        active_document_id = document_id
        
        return UploadResponse(
            document_id=document_id,
            filename=file.filename,
            pages=num_pages,
            chunks=len(chunks),
            summary=summary_result,
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


@app.post("/analyze")
async def analyze_insurance_policy(request: AnalysisRequest):
    """
    Analyze insurance policy and generate downloadable PDF report.
    
    1. Get document and its full text
    2. Extract insurance policy information using InsuranceAnalyzer
    3. Generate professional PDF report
    4. Return PDF file for download
    """
    try:
        document_id = request.document_id
        
        # Validate document exists
        if document_id not in documents_metadata:
            raise HTTPException(status_code=404, detail="Document not found")
        
        metadata = documents_metadata[document_id]
        full_text = metadata.get("full_text", "")
        filename = metadata["filename"]
        
        if not full_text:
            raise HTTPException(status_code=400, detail="Document text not available")
        
        print(f"Analyzing insurance policy: {document_id}")
        
        # Extract insurance policy information
        analysis = insurance_analyzer.extract_policy_information(full_text)
        
        # Get summary for report
        summary_text = metadata["summary"].get("summary", "") if metadata.get("summary") else ""
        
        # Generate PDF report
        pdf_bytes = report_generator.generate_policy_report(
            filename=filename,
            analysis_data=analysis,
            summary_text=summary_text
        )
        
        # Save analysis in metadata
        metadata["analysis"] = analysis
        
        # Return PDF file
        clean_filename = filename.replace('.pdf', '')
        return FileResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            filename=f"{clean_filename}_Analysis_Report.pdf"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing document: {str(e)}")


@app.get("/analysis/{document_id}")
async def get_analysis(document_id: str):
    """Get the stored analysis data for a document (JSON)."""
    try:
        if document_id not in documents_metadata:
            raise HTTPException(status_code=404, detail="Document not found")
        
        metadata = documents_metadata[document_id]
        
        if "analysis" not in metadata:
            raise HTTPException(status_code=404, detail="No analysis available. Please run analyze endpoint first.")
        
        return {
            "document_id": document_id,
            "filename": metadata["filename"],
            "analysis": metadata["analysis"],
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
