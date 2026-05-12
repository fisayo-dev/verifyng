# app/content_validator.py

from .database import get_institution_formats
import re
import logging
import json

logger = logging.getLogger(__name__)

# Cache formats in memory at startup (Cache with intent)
_cached_formats = None

BUILT_IN_FORMATS = [
    {
        "name": "West African Examinations Council",
        "cert_type": "WASSCE Result",
        "known_keywords": [
            "WEST AFRICAN",
            "EXAMINATIONS COUNCIL",
            "WAEC",
            "WASSCE",
            "CANDIDATE NAME",
            "EXAMINATION NUMBER",
        ],
    }
]

def get_formats_cached() -> list:
    """
    Load institution formats once at startup.
    Avoids hitting Supabase on every request.
    """
    global _cached_formats
    if _cached_formats is None:
        try:
            _cached_formats = get_institution_formats()
            logger.info(f"Loaded {len(_cached_formats)} institution formats")
        except Exception as e:
            logger.error(f"Failed to load formats: {e}")
            _cached_formats = []
    return BUILT_IN_FORMATS + _cached_formats


def validate_certificate_content(text: str) -> dict:
    """
    Validate extracted OCR text against known institution formats.
    
    Returns:
        content_score: 0-100
        flags: list of issues found
        detected_institution: name if found, None if not
        detected_cert_type: type if found, None if not
    """
    if not text or len(text.strip()) < 20:
        return {
            "content_score": 20,
            "flags": ["Insufficient text extracted from document"],
            "detected_institution": None,
            "detected_cert_type": None
        }

    text_upper = text.upper()
    flags = []
    score = 100
    detected_institution = None
    detected_cert_type = None

    # ── Check 1: Institution Recognition ──────────────────────────
    formats = get_formats_cached()
    institution_found = False

    for fmt in formats:
        keywords = fmt.get("known_keywords", [])
        if isinstance(keywords, str):
            keywords = json.loads(keywords)

        matches = [kw for kw in keywords if kw.upper() in text_upper]

        if len(matches) >= 2:  # At least 2 keywords must match
            institution_found = True
            detected_institution = fmt["name"]
            detected_cert_type = fmt["cert_type"]
            logger.info(f"Institution detected: {detected_institution}")
            break

    if not institution_found:
        score -= 25
        flags.append(
            "No recognized Nigerian institution found in document"
        )

    # ── Check 2: Certificate Keywords ─────────────────────────────
    cert_keywords = [
        "CERTIFICATE", "DIPLOMA", "DEGREE",
        "AWARDED", "CONFERRED", "HEREBY CERTIFY",
        "RESULT", "EXAMINATION", "PASSED",
        "WAEC", "WASSCE", "EXAMINATIONS COUNCIL"
    ]
    found_cert_keywords = [k for k in cert_keywords if k in text_upper]

    if not found_cert_keywords:
        score -= 20
        flags.append("No standard certificate language detected")

    # ── Check 3: Year Presence ─────────────────────────────────────
    years = list(dict.fromkeys(re.findall(r'\b(?:19|20)\d{2}\b', text)))
    if not years:
        score -= 10
        flags.append("No valid year found in document")
    else:
        year = int(years[0])
        if year < 1980 or year > 2026:
            score -= 15
            flags.append(f"Suspicious year detected: {year}")

    # ── Check 4: Name Presence ─────────────────────────────────────
    # Look for patterns like "THIS IS TO CERTIFY THAT [NAME]"
    name_patterns = [
        r"CERTIFY THAT\s+([A-Z\s]{5,40})",
        r"AWARDED TO\s+([A-Z\s]{5,40})",
        r"THIS IS TO CERTIFY\s+([A-Z\s]{5,40})",
        r"CANDIDATE NAME\s+([A-Z][A-Z\s.'-]{4,80})(?:\n|EXAMINATION|$)"
    ]
    name_found = any(re.search(p, text_upper) for p in name_patterns)
    if not name_found:
        score -= 10
        flags.append("Could not detect candidate name pattern")

    # ── Check 5: Text Length Sanity ────────────────────────────────
    word_count = len(text.split())
    if word_count < 30:
        score -= 15
        flags.append(
            f"Document text too short ({word_count} words) "
            "— may be low quality scan"
        )

    return {
        "content_score": max(0, score),
        "flags": flags,
        "detected_institution": detected_institution,
        "detected_cert_type": detected_cert_type,
        "word_count": word_count,
        "years_found": years if years else []
    }
