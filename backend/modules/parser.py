"""
PDF Parser Module
Extracts text from PDFs using PyMuPDF with OCR fallback for scanned pages.
Includes image preprocessing for better OCR accuracy on scanned documents.
"""

import fitz  # PyMuPDF
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import cv2
import numpy as np
import io
import os
from typing import Dict, List, Tuple


def preprocess_image_for_ocr(image: Image.Image) -> Image.Image:
    """
    Preprocess image to improve OCR accuracy.
    
    Applies:
    - Grayscale conversion
    - Contrast enhancement
    - Noise reduction
    - Thresholding
    
    Args:
        image: PIL Image
    
    Returns:
        Preprocessed PIL Image
    """
    try:
        # Convert to grayscale if not already
        if image.mode != 'L':
            image = image.convert('L')
        
        # Enhance contrast
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(2)  # Increase contrast
        
        # Enhance brightness
        enhancer = ImageEnhance.Brightness(image)
        image = enhancer.enhance(1.2)
        
        # Apply bilateral filter to reduce noise while keeping edges
        img_np = np.array(image)
        img_np = cv2.bilateralFilter(img_np, 11, 17, 17)
        image = Image.fromarray(img_np)
        
        # Apply sharpening filter
        image = image.filter(ImageFilter.SHARPEN)
        
        # Convert to binary using Otsu's method for better text clarity
        img_np = np.array(image)
        _, img_np = cv2.threshold(img_np, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        image = Image.fromarray(img_np)
        
        return image
    except Exception as e:
        print(f"  ⚠️  Image preprocessing failed: {e}, using original image")
        return image


def is_scanned_page(text: str, min_chars: int = 50) -> bool:
    """
    Detect if a page is scanned (image-based) by checking extracted text length.
    If text is too short, it's likely a scanned page.
    
    Args:
        text: Extracted text from page
        min_chars: Minimum characters to consider as searchable text
    
    Returns:
        True if page appears to be scanned
    """
    return len(text.strip()) < min_chars


def extract_text_with_ocr(page, use_preprocessing: bool = True) -> str:
    """
    Extract text from a page using Tesseract OCR with optional preprocessing.
    Used as fallback for scanned/image-based pages.
    
    Args:
        page: PyMuPDF page object
        use_preprocessing: Whether to preprocess image before OCR
    
    Returns:
        Extracted text string
    """
    try:
        # Convert page to image with higher DPI for better OCR accuracy
        pix = page.get_pixmap(matrix=fitz.Matrix(3, 3))  # 3x zoom
        
        # Convert to PIL Image
        img_data = pix.tobytes("ppm")
        img = Image.open(io.BytesIO(img_data))
        
        # Preprocess image if enabled
        if use_preprocessing:
            print(f"  → Preprocessing image for OCR...")
            img = preprocess_image_for_ocr(img)
        
        # Configure pytesseract for better results
        # OEM 3: Use both legacy and LSTM OCR engine modes
        # PSM 6: Assume a block of text
        custom_config = r'--oem 3 --psm 6 -l eng'
        
        # Run OCR
        text = pytesseract.image_to_string(img, config=custom_config)
        
        if text.strip():
            char_count = len(text.strip())
            print(f"  ✓ OCR extracted {char_count} characters")
        else:
            print(f"  ⚠️  OCR returned empty text, trying without preprocessing...")
            if use_preprocessing:
                # Retry without preprocessing
                img_data = pix.tobytes("ppm")
                img = Image.open(io.BytesIO(img_data))
                text = pytesseract.image_to_string(img, config=custom_config)
        
        return text
    except Exception as e:
        print(f"  ✗ OCR extraction failed: {e}")
        return ""


def parse_pdf(file_path: str) -> Dict[int, str]:
    """
    Parse PDF and extract text from all pages.
    Uses PyMuPDF for text extraction, falls back to OCR for scanned pages.
    
    Args:
        file_path: Path to PDF file
    
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
                print(f"  → Page {page_num + 1} detected as scanned, running OCR with preprocessing...")
                ocr_text = extract_text_with_ocr(page, use_preprocessing=True)
                
                # Use OCR text if it's better than PyMuPDF extraction
                if len(ocr_text.strip()) > text_length:
                    text = ocr_text
                    print(f"  → OCR provided better extraction ({len(ocr_text.strip())} chars)")
                else:
                    print(f"  → PyMuPDF extraction sufficient, OCR skipped")
            
            page_texts[page_num + 1] = text  # 1-indexed page numbers
        
        pdf_document.close()
        return page_texts
        
    except Exception as e:
        raise Exception(f"Error parsing PDF: {str(e)}")


def clean_text(text: str) -> str:
    """
    Clean and preprocess extracted text.
    Removes extra whitespace, normalizes line breaks.
    
    Args:
        text: Raw extracted text
    
    Returns:
        Cleaned text
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
    
    Args:
        file_path: Path to PDF file
    
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
