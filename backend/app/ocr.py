# backend/ocr.py

import pytesseract
from PIL import Image
from pdf2image import convert_from_path
import hashlib
import os
import numpy as np
import cv2

def compute_file_hash(file_bytes: bytes) -> str:
    """Generate unique hash for any file — used for deduplication"""
    return hashlib.sha256(file_bytes).hexdigest()

def check_image_quality(image: Image.Image) -> dict:
    """Reject blurry images before wasting compute"""

    
    img_array = np.array(image.convert('L'))  # Convert to grayscale
    laplacian_var = cv2.Laplacian(img_array, cv2.CV_64F).var()
    
    is_acceptable = bool(laplacian_var > 100)  # Convert numpy.bool_ to Python bool
    return {
        "quality_score": round(laplacian_var, 2),
        "is_acceptable": is_acceptable,  # Now JSON-serializable
        "message": "Good quality" if is_acceptable else "Image too blurry"
    }

def extract_text_from_image(image_path: str) -> dict:
    """Extract all text from a certificate image"""
    try:
        image = Image.open(image_path)
        
        # Check quality first
        quality = check_image_quality(image)
        if not quality["is_acceptable"]:
            return {
                "success": False,
                "error": "Image quality too low",
                "quality": quality
            }
        
        # Extract text
        text = pytesseract.image_to_string(image)
        
        # Extract with confidence scores
        data = pytesseract.image_to_data(
            image, 
            output_type=pytesseract.Output.DICT
        )
        
        # Calculate average confidence
        confidences = [
            int(c) for c in data['conf'] 
            if str(c).isdigit() and int(c) > 0
        ]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        return {
            "success": True,
            "text": text.strip(),
            "confidence": round(avg_confidence, 2),
            "word_count": len(text.split()),
            "quality": quality
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def extract_text_from_pdf(pdf_path: str) -> dict:
    """Extract text from a PDF certificate"""
    try:
        pages = convert_from_path(pdf_path, dpi=200)
        
        if not pages:
            return {"success": False, "error": "Could not read PDF"}
        
        # Process first page only (certificates are 1 page)
        first_page = pages[0]
        
        # Save temp image and extract
        temp_path = "/tmp/cert_page.jpg"
        first_page.save(temp_path, "JPEG")
        
        return extract_text_from_image(temp_path)
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def extract_text(file_path: str) -> dict:
    """Smart router — handles both images and PDFs"""
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext == ".pdf":
        return extract_text_from_pdf(file_path)
    elif ext in [".jpg", ".jpeg", ".png", ".tiff", ".bmp"]:
        return extract_text_from_image(file_path)
    else:
        return {"success": False, "error": f"Unsupported file type: {ext}"}
