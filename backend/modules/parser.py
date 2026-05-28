"""
PDF Parser Module
Extracts text from PDFs using PyMuPDF with OCR fallback for scanned pages.
"""

import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
from typing import Dict, List, Tuple


def is_scanned_page(text: str, min_chars: int = 50) -> bool:
    """
    Detect if a page is scanned (image-based) by checking extracted text length.
    If text is too short, it's likely a scanned page.
    """
    return len(text.strip()) < min_chars


def extract_text_with_ocr(page) -> str:
    """
    Extract text from a page using Tesseract OCR.
    Used as fallback for scanned/image-based pages.
    """
    try:
        # Convert page to image
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x zoom for better OCR
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        
        # Run OCR
        text = pytesseract.image_to_string(img)
        return text
    except Exception as e:
        print(f"OCR failed: {e}")
        return ""


def parse_pdf(file_path: str) -> Dict[int, str]:
    """
    Parse PDF and extract text from all pages.
    Uses PyMuPDF for text extraction, falls back to OCR for scanned pages.
    
    Returns:
        Dict mapping page number to extracted text
    """
    page_texts = {}
    
    try:
        pdf_document = fitz.open(file_path)
        
        for page_num in range(len(pdf_document)):
            page = pdf_document[page_num]
            
            # Try standard text extraction first
            text = page.get_text()
            
            # If page appears to be scanned, use OCR
            if is_scanned_page(text):
                print(f"Page {page_num + 1} detected as scanned, running OCR...")
                text = extract_text_with_ocr(page)
            
            page_texts[page_num + 1] = text  # 1-indexed page numbers
        
        pdf_document.close()
        return page_texts
        
    except Exception as e:
        raise Exception(f"Error parsing PDF: {str(e)}")


def clean_text(text: str) -> str:
    """
    Clean and preprocess extracted text.
    Removes extra whitespace, normalizes line breaks.
    """
    # Remove extra whitespace
    text = " ".join(text.split())
    
    # Normalize line breaks
    text = text.replace("\n", " ")
    
    # Remove multiple spaces
    while "  " in text:
        text = text.replace("  ", " ")
    
    return text.strip()


def get_page_wise_text(file_path: str) -> Dict[int, str]:
    """
    Extract and clean text from PDF, page by page.
    
    Returns:
        Dict with page numbers as keys and cleaned text as values
    """
    page_texts = parse_pdf(file_path)
    
    # Clean each page's text
    cleaned_texts = {
        page_num: clean_text(text)
        for page_num, text in page_texts.items()
    }
    
    return cleaned_texts
