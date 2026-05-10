# backend/app/extractor.py

import re
from typing import Optional


def extract_certificate_fields(text: str) -> dict:
    """
    Extract structured fields from raw OCR text.
    Returns a dict of detected certificate fields.
    """

    if not text:
        return {
            "success": False,
            "fields": {},
            "error": "No text provided"
        }

    fields = {}

    # --- Name ---
    name_patterns = [
        r"(?:this is to certify that|awarded to|presented to|conferred upon)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})",
        r"^([A-Z][A-Z\s]+)$",  # ALL CAPS name on its own line
    ]
    for pattern in name_patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if match:
            fields["recipient_name"] = match.group(1).strip()
            break

    # --- Institution ---
    institution_patterns = [
        r"(?:university|college|institute|school|polytechnic)\s+of\s+[\w\s]+",
        r"[\w\s]+(?:university|college|institute|school|polytechnic)",
    ]
    for pattern in institution_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            fields["institution"] = match.group(0).strip()
            break

    # --- Degree / Certificate Type ---
    degree_patterns = [
        r"(?:bachelor|master|doctor|diploma|certificate|degree)\s+(?:of|in)\s+[\w\s]+",
        r"(?:B\.Sc|M\.Sc|Ph\.D|HND|OND|B\.A|M\.A|MBA)[\w\s\.]*",
    ]
    for pattern in degree_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            fields["degree"] = match.group(0).strip()
            break

    # --- Date ---
    date_patterns = [
        r"\b(?:january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2},?\s+\d{4}\b",
        r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",
        r"\b\d{4}\b",  # year only fallback
    ]
    for pattern in date_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            fields["date_issued"] = match.group(0).strip()
            break

    # --- Certificate / Registration Number ---
    cert_num_patterns = [
        r"(?:cert(?:ificate)?\.?\s*(?:no|number|#)\.?\s*:?\s*)([\w\-\/]+)",
        r"(?:reg(?:istration)?\.?\s*(?:no|number|#)\.?\s*:?\s*)([\w\-\/]+)",
        r"(?:matric(?:ulation)?\.?\s*(?:no|number|#)\.?\s*:?\s*)([\w\-\/]+)",
    ]
    for pattern in cert_num_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            fields["certificate_number"] = match.group(1).strip()
            break

    return {
        "success": True,
        "fields": fields,
        "fields_found": len(fields),
        "raw_text_length": len(text)
    }


def generate_verification_summary(fields: Optional[dict], confidence: float) -> dict:
    """
    Generate a human-readable verification verdict
    based on extracted fields and OCR confidence.
    """

    if not fields:
        return {
            "verdict": "UNVERIFIABLE",
            "confidence_score": 0,
            "reason": "No fields could be extracted from the certificate."
        }

    score = 0
    reasons = []

    # Score based on fields found
    key_fields = ["recipient_name", "institution", "degree", "date_issued"]
    found = [f for f in key_fields if f in fields]
    score += len(found) * 20  # 20 points per key field (max 80)

    # Score based on OCR confidence
    if confidence >= 80:
        score += 20
    elif confidence >= 60:
        score += 10

    # Verdict
    if score >= 80:
        verdict = "LIKELY_AUTHENTIC"
    elif score >= 50:
        verdict = "NEEDS_REVIEW"
    else:
        verdict = "SUSPICIOUS"

    if found:
        reasons.append(f"Found fields: {', '.join(found)}")
    if confidence < 60:
        reasons.append("Low OCR confidence — document may be blurry or low resolution")

    return {
        "verdict": verdict,
        "confidence_score": score,
        "fields_detected": found,
        "missing_fields": [f for f in key_fields if f not in fields],
        "reason": ". ".join(reasons) if reasons else "Standard verification passed."
    }