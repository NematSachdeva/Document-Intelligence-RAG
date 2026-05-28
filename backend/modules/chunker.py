"""
Text Chunking Module
Splits extracted text into semantic chunks with metadata preservation.
"""

from typing import List, Dict


class Chunk:
    """Represents a text chunk with metadata."""
    
    def __init__(self, text: str, page_number: int, chunk_id: str):
        self.text = text
        self.page_number = page_number
        self.chunk_id = chunk_id
    
    def to_dict(self) -> Dict:
        return {
            "text": self.text,
            "page_number": self.page_number,
            "chunk_id": self.chunk_id
        }


def chunk_text(
    page_texts: Dict[int, str],
    chunk_size: int = 500,
    overlap: int = 100
) -> List[Chunk]:
    """
    Split text into chunks with overlap, preserving page metadata.
    
    Args:
        page_texts: Dict mapping page numbers to text
        chunk_size: Size of each chunk in characters
        overlap: Overlap between consecutive chunks
    
    Returns:
        List of Chunk objects with metadata
    """
    chunks = []
    chunk_counter = 0
    
    for page_num in sorted(page_texts.keys()):
        text = page_texts[page_num]
        
        # Split text into chunks with overlap
        for i in range(0, len(text), chunk_size - overlap):
            chunk_text = text[i : i + chunk_size]
            
            if len(chunk_text.strip()) > 0:  # Skip empty chunks
                chunk_id = f"page_{page_num}_chunk_{chunk_counter}"
                chunk = Chunk(
                    text=chunk_text,
                    page_number=page_num,
                    chunk_id=chunk_id
                )
                chunks.append(chunk)
                chunk_counter += 1
    
    return chunks


def get_chunks_with_metadata(chunks: List[Chunk]) -> tuple:
    """
    Extract texts and metadata from chunks for embedding storage.
    
    Returns:
        Tuple of (texts, metadatas, ids)
    """
    texts = [chunk.text for chunk in chunks]
    metadatas = [
        {
            "page_number": chunk.page_number,
            "chunk_id": chunk.chunk_id
        }
        for chunk in chunks
    ]
    ids = [chunk.chunk_id for chunk in chunks]
    
    return texts, metadatas, ids
