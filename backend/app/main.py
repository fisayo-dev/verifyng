# backend/app/main.py

import os

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import aiofiles
import uuid

from .ela import perform_ela, check_metadata_consistency, analyze_visual_consistency
from .ocr import extract_text, compute_file_hash
from .extractor import extract_certificate_fields, generate_verification_summary
import uvicorn

app = FastAPI(
    title="VerifyNG API",
    description="AI-powered certificate verification",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "/tmp/verifyng_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_TYPES = {
    "image/jpeg", "image/png", "image/tiff",
    "application/pdf"
}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


# ─────────────────────────────────────────
# HEALTH
# ─────────────────────────────────────────

@app.get("/")
def root():
    return {
        "message": "VerifyNG API is live",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "version": "1.0.0",
        "service": "VerifyNG"
    }


# ─────────────────────────────────────────
# TEST ENDPOINTS (remove before production)
# ─────────────────────────────────────────

@app.get("/test-ocr")
def test_ocr():
    """Quick OCR test — remove before production"""
    image_path = os.path.join(os.path.dirname(__file__), "..", "test_cert.jpg")
    result = extract_text(image_path)
    return result


@app.get("/test-ela")
def test_ela():
    """Test ELA on both real and fake certificates"""

    results = {}
    sample_dir = os.path.join(os.path.dirname(__file__), "..")

    real_cert_path = os.path.join(sample_dir, "test_cert.jpg")   # real cert
    fake_cert_path = os.path.join(sample_dir, "fake_cert.jpg")   # fake cert

    if os.path.exists(real_cert_path):
        ela    = perform_ela(real_cert_path)
        meta   = check_metadata_consistency(real_cert_path)
        visual = analyze_visual_consistency(real_cert_path)
        results["real_cert"] = {
            "ela_score":      ela.get("anomaly_score"),
            "risk_level":     ela.get("risk_level"),
            "ela_flags":      ela.get("flags"),
            "metadata_flags": meta.get("flags"),
            "visual_flags":   visual.get("flags"),
        }

    if os.path.exists(fake_cert_path):
        ela    = perform_ela(fake_cert_path)
        meta   = check_metadata_consistency(fake_cert_path)
        visual = analyze_visual_consistency(fake_cert_path)
        results["fake_cert"] = {
            "ela_score":      ela.get("anomaly_score"),
            "risk_level":     ela.get("risk_level"),
            "ela_flags":      ela.get("flags"),
            "metadata_flags": meta.get("flags"),
            "visual_flags":   visual.get("flags"),
        }

    return results


# ─────────────────────────────────────────
# MAIN VERIFY ENDPOINT
# ─────────────────────────────────────────

@app.post("/verify")
async def verify_certificate(file: UploadFile = File(...)):
    """
    Main endpoint.
    Upload a certificate image or PDF.
    Returns extracted fields + verification verdict.
    """

    # --- Validation ---
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed: {file.content_type}. Use JPG, PNG, or PDF."
        )

    file_bytes = await file.read()

    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail="File too large. Maximum size is 10MB."
        )

    # --- Save file temporarily ---
    file_id  = str(uuid.uuid4())
    ext      = os.path.splitext(file.filename)[1] or ".jpg"
    temp_path = os.path.join(UPLOAD_DIR, f"{file_id}{ext}")

    async with aiofiles.open(temp_path, "wb") as f:
        await f.write(file_bytes)

    try:
        # Step 1: Hash
        file_hash = compute_file_hash(file_bytes)

        # Step 2: OCR
        ocr_result = extract_text(temp_path)
        if not ocr_result["success"]:
            raise HTTPException(
                status_code=422,
                detail=f"Could not read certificate: {ocr_result['error']}"
            )

        # Step 3: AI Field Extraction
        extraction_result = extract_certificate_fields(ocr_result["text"])

        # Step 4: ELA Tamper Detection
        ela    = perform_ela(temp_path)
        meta   = check_metadata_consistency(temp_path)
        visual = analyze_visual_consistency(temp_path)

        # Step 5: Verification Summary
        summary = generate_verification_summary(
            fields=extraction_result.get("fields"),
            confidence=ocr_result.get("confidence", 0)
        )

        return {
            "request_id": file_id,
            "file_hash":  file_hash,
            "filename":   file.filename,
            "ocr": {
                "text":       ocr_result["text"],
                "confidence": ocr_result["confidence"],
                "word_count": ocr_result["word_count"],
                "quality":    ocr_result["quality"]
            },
            "extraction": extraction_result,
            "tamper_detection": {
                "ela_score":      ela.get("anomaly_score"),
                "risk_level":     ela.get("risk_level"),
                "ela_flags":      ela.get("flags"),
                "metadata_flags": meta.get("flags"),
                "visual_flags":   visual.get("flags"),
            },
            "verification": summary
        }

    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


if __name__ == "__main__":
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)