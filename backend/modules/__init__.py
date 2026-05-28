"""
PDF Assistant Modules
Core modules for PDF processing, embedding, and QA.
"""

from .parser import get_page_wise_text, parse_pdf, clean_text
from .chunker import chunk_text, get_chunks_with_metadata, Chunk
from .embeddings import EmbeddingManager
from .qa import QAEngine
from .summarizer import Summarizer

__all__ = [
    "get_page_wise_text",
    "parse_pdf",
    "clean_text",
    "chunk_text",
    "get_chunks_with_metadata",
    "Chunk",
    "EmbeddingManager",
    "QAEngine",
    "Summarizer",
]
