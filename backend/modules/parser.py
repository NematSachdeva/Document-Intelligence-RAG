"""
PDF Parser Module
Extracts text from PDFs using PyMuPDF with OCR fallback for scanned pages.
"""

import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
import os
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
        # Convert page to image with higher DPI for better OCR accuracy
        pix = page.get_pixmap(matrix=fitz.Matrix(3, 3))  # 3x zoom for better OCR
        
        # Convert to PIL Image
        img_data = pix.tobytes("ppm")
        img = Image.open(io.BytesIO(img_data))
        
        # Configure pytesseract for better results
        custom_config = r'--oem 3 --psm 6'
        
        # Run OCR
        text = pytesseract.image_to_string(img, config=custom_config)
        
        if text.strip():
            print(f"  ✓ OCR extracted {len(text.strip())} characters")
        else:
            print(f"  ⚠️  OCR returned empty text")
        
        return text
    except Exception as e:
        print(f"  ✗ OCR failed: {e}")
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
        total_pages = len(pdf_document)
        print(f"Processing PDF with {total_pages} pages...")
        
        for page_num in range(total_pages):
            page = pdf_document[page_num]
            
            # Try standard text extraction first
            text = page.get_text()
            text_length = len(text.strip())
            
            print(f"Page {page_num + 1}: Extracted {text_length} characters via PyMuPDF")
            
            # If page appears to be scanned, use OCR
            if is_scanned_page(text):
                print(f"  → Page {page_num + 1} detected as scanned, running OCR...")
                ocr_text = extract_text_with_ocr(page)
                
                # Use OCR text if it's better than PyMuPDF extraction
                if len(ocr_text.strip()) > text_length:
                    text = ocr_text
                    print(f"  → Using OCR text ({len(ocr_text.strip())} chars)")
                else:
                    print(f"  → OCR didn't improve extraction, using PyMuPDF")
            
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
