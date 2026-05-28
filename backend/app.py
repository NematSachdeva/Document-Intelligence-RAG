"""
FastAPI Application
Main entry point for the PDF Document Assistant.
Orchestrates PDF processing, embedding generation, and QA.
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List
import os
import shutil
import uuid
from dotenv import load_dotenv

# Import modules
from modules.parser import get_page_wise_text
from modules.chunker import chunk_text, get_chunks_with_metadata
from modules.embeddings import EmbeddingManager
from modules.qa import QAEngine
from modules.summarizer import Summarizer

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

# Store document metadata in memory (in production, use database)
documents_metadata = {}


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
    
    1. Save PDF
    2. Extract text with OCR fallback
    3. Create chunks
    4. Generate embeddings
    5. Generate summary
    """
    try:
        # Validate file
        if not file.filename.endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
        if file.size and file.size > MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail="File too large")
        
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
        
        # Store metadata
        documents_metadata[document_id] = {
            "filename": file.filename,
            "pages": num_pages,
            "chunks": len(chunks),
            "summary": summary_result,
            "collection_name": collection_name
        }
        
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
