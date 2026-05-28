# PDF Document Assistant

A full-stack AI-powered PDF document assistant with semantic search, question answering, and document summarization.

## Features

- 📄 **PDF Upload & Processing**: Upload PDFs and automatically extract text
- 🔍 **OCR Support**: Automatic fallback to Tesseract OCR for scanned documents
- 🧠 **Semantic Search**: Find relevant information using AI embeddings
- 💬 **Question Answering**: Ask questions and get accurate answers with citations
- 📋 **Document Summarization**: Automatic generation of summaries and key points
- 🎯 **Source Citations**: Every answer includes page references and source information
- 🚀 **Production-Ready**: Clean architecture, proper error handling, and scalable design

## Tech Stack

### Backend
- **FastAPI**: Modern Python web framework
- **PyMuPDF**: PDF text extraction
- **Tesseract OCR**: Scanned document processing
- **Sentence Transformers**: Embedding generation
- **ChromaDB**: Vector database for semantic search
- **LangChain**: LLM integration
- **Groq API**: Large language model (Mixtral 8x7B)

### Frontend
- **Next.js**: React framework
- **TailwindCSS**: Styling
- **Axios**: API client
- **Lucide React**: Icons

## Project Structure

```
pdf-assistant/
├── backend/
│   ├── app.py                 # FastAPI application
│   ├── requirements.txt       # Python dependencies
│   ├── .env.example          # Environment variables template
│   ├── uploads/              # Uploaded PDFs
│   ├── chroma_db/            # Vector database
│   └── modules/
│       ├── parser.py         # PDF text extraction
│       ├── chunker.py        # Text chunking
│       ├── embeddings.py     # Embedding generation
│       ├── qa.py             # Question answering
│       └── summarizer.py     # Document summarization
└── frontend/
    ├── package.json
    ├── pages/
    │   └── index.tsx         # Main application
    ├── components/
    │   ├── FileUpload.tsx
    │   ├── Summary.tsx
    │   └── ChatInterface.tsx
    ├── lib/
    │   └── api.ts            # API client
    └── styles/
        └── globals.css
```

## Installation

### Prerequisites

- Python 3.9+
- Node.js 16+
- Tesseract OCR (for scanned PDF support)

### Install Tesseract

**macOS:**
```bash
brew install tesseract
```

**Ubuntu/Debian:**
```bash
sudo apt-get install tesseract-ocr
```

**Windows:**
Download from: https://github.com/UB-Mannheim/tesseract/wiki

### Backend Setup

1. Navigate to backend directory:
```bash
cd pdf-assistant/backend
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create `.env` file:
```bash
cp .env.example .env
```

5. Configure environment variables in `.env`:

**For Google Gemini:**
```
GEMINI_API_KEY=your_gemini_api_key_here
LLM_PROVIDER=gemini
```

**For OpenAI:**
```
OPENAI_API_KEY=your_openai_api_key_here
LLM_PROVIDER=openai
```

6. Run the backend:
```bash
python app.py
```

The API will be available at `http://localhost:8000`

### Frontend Setup

1. Navigate to frontend directory:
```bash
cd pdf-assistant/frontend
```

2. Install dependencies:
```bash
npm install
```

3. Create `.env.local` file:
```bash
cp .env.example .env.local
```

4. Run the development server:
```bash
npm run dev
```

The application will be available at `http://localhost:3000`

## API Endpoints

### Upload PDF
```
POST /upload
Content-Type: multipart/form-data

Response:
{
  "document_id": "string",
  "filename": "string",
  "pages": number,
  "chunks": number,
  "summary": {
    "summary": "string",
    "key_points": ["string"],
    "main_topics": ["string"],
    "success": boolean
  },
  "success": boolean
}
```

### Ask Question
```
POST /ask
Content-Type: application/json

Request:
{
  "document_id": "string",
  "question": "string"
}

Response:
{
  "answer": "string",
  "citations": [
    {
      "source_id": number,
      "page_number": number,
      "chunk_id": "string"
    }
  ],
  "success": boolean
}
```

### Get Summary
```
GET /summary/{document_id}

Response:
{
  "summary": "string",
  "key_points": ["string"],
  "main_topics": ["string"],
  "success": boolean
}
```

### List Documents
```
GET /documents

Response:
{
  "documents": [
    {
      "document_id": "string",
      "filename": "string",
      "pages": number,
      "chunks": number
    }
  ]
}
```

### Delete Document
```
DELETE /documents/{document_id}

Response:
{
  "success": boolean,
  "message": "string"
}
```

### Health Check
```
GET /health

Response:
{
  "status": "healthy",
  "llm_provider": "string",
  "documents_loaded": number
}
```

## How It Works

### PDF Processing Pipeline

1. **Upload**: User uploads a PDF file
2. **Text Extraction**: PyMuPDF extracts text from each page
3. **Scanned Detection**: System detects if pages are scanned (low text content)
4. **OCR Fallback**: Tesseract OCR processes scanned pages
5. **Text Cleaning**: Extracted text is cleaned and normalized
6. **Chunking**: Text is split into 500-character chunks with 100-character overlap
7. **Embedding**: Chunks are converted to embeddings using sentence-transformers
8. **Storage**: Embeddings are stored in ChromaDB for semantic search
9. **Summarization**: LLM generates document summary and key points

### Question Answering Pipeline

1. **Query Embedding**: User question is converted to embedding
2. **Semantic Search**: Top 5 similar chunks are retrieved from ChromaDB
3. **Context Building**: Retrieved chunks are formatted with citations
4. **LLM Processing**: Question and context are sent to LLM
5. **Answer Generation**: LLM generates grounded answer with source references
6. **Response**: Answer with citations is returned to user

## Configuration

### Chunking Strategy
- **Chunk Size**: 500 characters
- **Overlap**: 100 characters
- Preserves page numbers and chunk IDs in metadata

### Embedding Model
- **Model**: `all-MiniLM-L6-v2` (384-dimensional embeddings)
- **Provider**: Sentence Transformers
- **Storage**: ChromaDB with cosine similarity

### LLM Configuration
- **Temperature**: 0.3 (for consistent, grounded answers)
- **Max Tokens**: Default (varies by model)
- **Providers**: Google Gemini or OpenAI

## Performance Optimization

### OCR Strategy
- Only OCR pages with minimal extracted text (< 50 characters)
- Skips OCR for text-based PDFs to save processing time

### Caching
- Embeddings are cached in ChromaDB
- Summaries are cached after generation
- Document metadata is stored in memory

### Scalability
- ChromaDB can be migrated to Pinecone for cloud deployment
- FastAPI supports async operations
- Frontend uses efficient React patterns

## Troubleshooting

### Backend Issues

**"GEMINI_API_KEY not set"**
- Ensure `.env` file exists in backend directory
- Check that `GEMINI_API_KEY` is set correctly

**"Tesseract not found"**
- Install Tesseract OCR for your OS
- On macOS: `brew install tesseract`

**"ChromaDB connection error"**
- Ensure `chroma_db/` directory has write permissions
- Check disk space availability

### Frontend Issues

**"Cannot connect to backend API"**
- Ensure backend is running on `http://localhost:8000`
- Check `NEXT_PUBLIC_API_URL` in `.env.local`
- Verify CORS is enabled in FastAPI

**"PDF upload fails"**
- Check file size (max 50MB)
- Ensure file is valid PDF
- Check backend logs for detailed error

## Future Enhancements

- [ ] Support for multiple PDFs in single session
- [ ] Streaming responses for faster feedback
- [ ] Advanced filtering and search options
- [ ] User authentication and document management
- [ ] Export answers and summaries to PDF
- [ ] Multi-language support
- [ ] Custom embedding models
- [ ] Fine-tuned LLM models
- [ ] Document comparison features
- [ ] Batch processing

## License

MIT

## Support

For issues and questions, please open an issue on GitHub.
