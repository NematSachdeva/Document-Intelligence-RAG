# Architecture Overview

## System Design

The PDF Document Assistant follows a clean, modular architecture with clear separation of concerns.

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (Next.js)                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │  FileUpload  │  │   Summary    │  │ChatInterface │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
│         │                 │                  │               │
│         └─────────────────┼──────────────────┘               │
│                           │                                  │
│                      API Client (axios)                      │
└─────────────────────────────────────────────────────────────┘
                            │
                    HTTP/REST API
                            │
┌─────────────────────────────────────────────────────────────┐
│                   Backend (FastAPI)                          │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                    app.py                            │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────────────┐   │   │
│  │  │ /upload  │  │ /ask     │  │ /summary, etc.   │   │   │
│  │  └──────────┘  └──────────┘  └──────────────────┘   │   │
│  └──────────────────────────────────────────────────────┘   │
│                           │                                  │
│  ┌────────────────────────┼────────────────────────────┐    │
│  │                        │                            │    │
│  ▼                        ▼                            ▼    │
│ ┌──────────┐  ┌──────────────┐  ┌──────────────────┐       │
│ │ parser   │  │  chunker     │  │  embeddings      │       │
│ │          │  │              │  │                  │       │
│ │ • Extract│  │ • Split text │  │ • Generate       │       │
│ │   text   │  │ • Preserve   │  │   embeddings     │       │
│ │ • OCR    │  │   metadata   │  │ • Store in       │       │
│ │ • Clean  │  │ • Overlap    │  │   ChromaDB       │       │
│ └──────────┘  └──────────────┘  └──────────────────┘       │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                                                      │   │
│  ▼                                                      ▼   │
│ ┌──────────────────────┐  ┌──────────────────────────┐     │
│ │        qa.py         │  │    summarizer.py         │     │
│ │                      │  │                          │     │
│ │ • Retrieve chunks    │  │ • Generate summary       │     │
│ │ • Build context      │  │ • Extract key points     │     │
│ │ • Call LLM           │  │ • Identify topics        │     │
│ │ • Format answer      │  │ • Parse LLM response     │     │
│ └──────────────────────┘  └──────────────────────────┘     │
│                                                              │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
    ┌────────┐         ┌──────────┐      ┌──────────┐
    │ ChromaDB│         │ Gemini/  │      │ File    │
    │ Vector  │         │ OpenAI   │      │ System  │
    │ Store   │         │ LLM      │      │ (PDFs)  │
    └────────┘         └──────────┘      └──────────┘
```

## Module Responsibilities

### 1. Parser Module (`parser.py`)

**Purpose**: Extract text from PDFs with intelligent OCR fallback

**Key Functions**:
- `parse_pdf()`: Main extraction function
- `is_scanned_page()`: Detect scanned pages
- `extract_text_with_ocr()`: Run Tesseract OCR
- `clean_text()`: Normalize extracted text
- `get_page_wise_text()`: Complete extraction pipeline

**Flow**:
```
PDF File
   │
   ├─→ PyMuPDF extraction
   │
   ├─→ Check if text is sufficient
   │
   ├─→ If insufficient: Run OCR
   │
   ├─→ Clean text
   │
   └─→ Return page-wise text dict
```

**Key Design Decisions**:
- Only OCR pages with < 50 characters (performance optimization)
- 2x zoom for OCR (better accuracy)
- Aggressive text cleaning (normalize whitespace)

### 2. Chunker Module (`chunker.py`)

**Purpose**: Split text into semantic chunks with metadata

**Key Classes**:
- `Chunk`: Represents a text chunk with metadata

**Key Functions**:
- `chunk_text()`: Split text with overlap
- `get_chunks_with_metadata()`: Extract texts and metadata

**Configuration**:
- Chunk size: 500 characters
- Overlap: 100 characters
- Metadata: page number, chunk ID

**Flow**:
```
Page-wise text
   │
   ├─→ Iterate through pages
   │
   ├─→ Split each page into chunks
   │
   ├─→ Preserve page metadata
   │
   ├─→ Add chunk IDs
   │
   └─→ Return list of Chunk objects
```

**Key Design Decisions**:
- Fixed chunk size for consistency
- Overlap prevents context loss at boundaries
- Metadata preservation enables source citations

### 3. Embeddings Module (`embeddings.py`)

**Purpose**: Generate embeddings and manage vector storage

**Key Class**:
- `EmbeddingManager`: Handles embeddings and ChromaDB operations

**Key Methods**:
- `generate_embeddings()`: Create embeddings using sentence-transformers
- `store_embeddings()`: Save to ChromaDB
- `retrieve_similar_chunks()`: Semantic search

**Configuration**:
- Model: `all-MiniLM-L6-v2` (384-dim, fast, accurate)
- Distance metric: Cosine similarity
- Top-k retrieval: 5 chunks

**Flow**:
```
Text chunks
   │
   ├─→ Generate embeddings (sentence-transformers)
   │
   ├─→ Store in ChromaDB with metadata
   │
   └─→ Ready for semantic search

Query
   │
   ├─→ Generate query embedding
   │
   ├─→ Search ChromaDB (cosine similarity)
   │
   └─→ Return top-k results with metadata
```

**Key Design Decisions**:
- Persistent ChromaDB for local storage
- Cosine similarity for semantic matching
- Metadata preservation for citations

### 4. QA Module (`qa.py`)

**Purpose**: Answer questions using retrieved context and LLM

**Key Class**:
- `QAEngine`: Orchestrates QA pipeline

**Key Methods**:
- `build_context()`: Format retrieved chunks with citations
- `generate_answer()`: Call LLM with grounded prompt
- `answer_question()`: Complete QA pipeline

**Configuration**:
- Temperature: 0.3 (consistent, grounded answers)
- Top-k chunks: 5
- LLM providers: Gemini or OpenAI

**Flow**:
```
User question
   │
   ├─→ Retrieve similar chunks from ChromaDB
   │
   ├─→ Build context with citations
   │
   ├─→ Create grounded prompt
   │
   ├─→ Call LLM (Gemini/OpenAI)
   │
   ├─→ Parse response
   │
   └─→ Return answer with citations
```

**Key Design Decisions**:
- Grounded prompting (answer only from context)
- Citation tracking for transparency
- Low temperature for consistency

### 5. Summarizer Module (`summarizer.py`)

**Purpose**: Generate document summaries and key points

**Key Class**:
- `Summarizer`: Generates summaries using LLM

**Key Methods**:
- `generate_summary()`: Create summary, key points, topics
- `_parse_summary_response()`: Parse LLM output

**Configuration**:
- Temperature: 0.3
- Max input: 3000 characters (efficiency)

**Flow**:
```
Full document text
   │
   ├─→ Limit to first 3000 chars
   │
   ├─→ Create structured prompt
   │
   ├─→ Call LLM
   │
   ├─→ Parse response
   │
   └─→ Return summary, key points, topics
```

**Key Design Decisions**:
- Structured output format (easier parsing)
- Limited input for efficiency
- Separate extraction of summary, points, topics

### 6. FastAPI Application (`app.py`)

**Purpose**: Orchestrate complete workflow and expose REST API

**Key Endpoints**:
- `POST /upload`: Process PDF
- `POST /ask`: Answer question
- `GET /summary/{document_id}`: Get summary
- `GET /documents`: List documents
- `DELETE /documents/{document_id}`: Delete document
- `GET /health`: Health check

**Flow**:
```
Upload Request
   │
   ├─→ Validate file
   ├─→ Save PDF
   ├─→ Extract text (parser)
   ├─→ Create chunks (chunker)
   ├─→ Generate embeddings (embeddings)
   ├─→ Generate summary (summarizer)
   ├─→ Store metadata
   └─→ Return response

Question Request
   │
   ├─→ Retrieve chunks (embeddings)
   ├─→ Generate answer (qa)
   └─→ Return answer with citations
```

**Key Design Decisions**:
- In-memory metadata storage (can be replaced with DB)
- CORS enabled for all origins
- Proper error handling and validation

## Data Flow

### Upload Pipeline

```
1. User uploads PDF
   ↓
2. Backend receives file
   ↓
3. Parser extracts text
   ├─ PyMuPDF for text
   └─ Tesseract for scanned pages
   ↓
4. Chunker splits text
   ├─ 500-char chunks
   └─ 100-char overlap
   ↓
5. Embeddings generated
   ├─ Sentence-transformers
   └─ Stored in ChromaDB
   ↓
6. Summarizer creates summary
   ├─ Summary text
   ├─ Key points
   └─ Main topics
   ↓
7. Response sent to frontend
   ├─ Document ID
   ├─ Metadata
   └─ Summary
```

### Question Answering Pipeline

```
1. User asks question
   ↓
2. Question embedding generated
   ↓
3. Semantic search in ChromaDB
   ├─ Top 5 similar chunks
   └─ With metadata
   ↓
4. Context built with citations
   ↓
5. LLM called with grounded prompt
   ├─ System: Answer only from context
   ├─ User: Question + context
   └─ Temperature: 0.3
   ↓
6. Answer parsed and formatted
   ├─ Answer text
   └─ Citations
   ↓
7. Response sent to frontend
```

## Technology Choices

### Why PyMuPDF?
- Fast text extraction
- Handles complex PDFs well
- Good balance of speed and accuracy

### Why Tesseract OCR?
- Open source and free
- Reliable for scanned documents
- Easy integration with PyMuPDF

### Why Sentence Transformers?
- Fast embedding generation
- Good quality embeddings
- Lightweight and easy to deploy

### Why ChromaDB?
- Simple local vector storage
- Easy to migrate to Pinecone
- Good for development and small deployments

### Why FastAPI?
- Modern Python framework
- Built-in async support
- Automatic API documentation
- Type hints and validation

### Why Next.js?
- React framework with SSR
- Great developer experience
- Easy deployment
- Built-in optimization

## Scalability Considerations

### Current Limitations
- In-memory metadata storage
- Local file uploads
- Single-machine deployment

### Scaling Strategies

**Database**:
```python
# Replace in-memory dict with PostgreSQL
from sqlalchemy import create_engine
engine = create_engine("postgresql://...")
```

**Vector Store**:
```python
# Migrate from ChromaDB to Pinecone
from pinecone import Pinecone
pc = Pinecone(api_key="...")
```

**File Storage**:
```python
# Use S3 instead of local filesystem
import boto3
s3 = boto3.client('s3')
```

**Async Processing**:
```python
# Use Celery for background tasks
from celery import Celery
app = Celery('pdf_assistant')
```

## Performance Optimization

### Current Optimizations
1. **Selective OCR**: Only OCR pages with minimal text
2. **Embedding Caching**: Store embeddings in ChromaDB
3. **Metadata Caching**: Store in memory
4. **Async API**: FastAPI async endpoints

### Potential Improvements
1. **Response Streaming**: Stream LLM responses
2. **Batch Processing**: Process multiple PDFs
3. **Compression**: Compress embeddings
4. **Indexing**: Add database indexes
5. **Caching**: Redis for metadata

## Security Considerations

### Current Implementation
- File size validation (50MB limit)
- File type validation (PDF only)
- CORS enabled for development

### Production Recommendations
1. **Authentication**: Add user authentication
2. **Authorization**: Implement access control
3. **Rate Limiting**: Add rate limits
4. **Input Validation**: Validate all inputs
5. **CORS**: Restrict to specific origins
6. **HTTPS**: Use HTTPS in production
7. **Secrets**: Use environment variables
8. **Logging**: Log all operations

## Testing Strategy

### Unit Tests
```python
# Test parser
def test_parse_pdf():
    texts = parse_pdf("test.pdf")
    assert len(texts) > 0

# Test chunker
def test_chunk_text():
    chunks = chunk_text({"1": "text"})
    assert len(chunks) > 0
```

### Integration Tests
```python
# Test complete pipeline
def test_upload_and_ask():
    # Upload PDF
    # Ask question
    # Verify answer
```

### E2E Tests
```python
# Test frontend to backend
# Upload PDF via UI
# Ask question via UI
# Verify answer displayed
```

## Deployment

### Development
```bash
# Backend
python app.py

# Frontend
npm run dev
```

### Production
```bash
# Backend
gunicorn -w 4 app:app

# Frontend
npm run build && npm start
```

### Docker
```bash
# Build and run containers
docker-compose up
```

## Monitoring

### Metrics to Track
- PDF processing time
- Embedding generation time
- LLM response time
- API response time
- Error rates
- Document count
- User count

### Logging
```python
import logging
logger = logging.getLogger(__name__)
logger.info("Processing PDF: %s", filename)
```

## Future Enhancements

1. **Multi-PDF Support**: Compare across documents
2. **Streaming**: Stream LLM responses
3. **Fine-tuning**: Fine-tune embeddings
4. **Custom Models**: Support custom LLMs
5. **Advanced Search**: Filters, date ranges
6. **Export**: Export answers to PDF
7. **Collaboration**: Share documents
8. **Analytics**: Track usage patterns
