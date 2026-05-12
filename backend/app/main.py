# backend/app/main.py

import os
import logging
import tempfile
import uuid

from fastapi import BackgroundTasks, FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import aiofiles

from .ela import perform_ela, check_metadata_consistency, analyze_visual_consistency, calculate_visual_trust_score
from .ocr import extract_text, compute_file_hash
from .content_validator import validate_certificate_content
from .database import (
    create_payment_record,
    create_verification_job,
    get_verification_result,
    update_verification_result,
)
import uvicorn

logger = logging.getLogger(__name__)

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

UPLOAD_DIR = os.environ.get(
    "VERIFYNG_UPLOAD_DIR",
    os.path.join(tempfile.gettempdir(), "verifyng_uploads")
)
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_TYPES = {
    "image/jpeg", "image/png", "image/tiff",
    "application/pdf"
}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
PAYMENT_AMOUNT = 500
CURRENCY = "NGN"


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
async def verify_certificate(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """
    Main endpoint.
    Upload a certificate image or PDF.
    Creates a verification job and starts processing in the background.
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

    file_hash = compute_file_hash(file_bytes)
    job = create_verification_job(file_hash, file.filename)
    job_id = job["job_id"]
    squad_ref = f"VNG-{job_id[:8]}"
    create_payment_record(squad_ref, job_id)

    # --- Save file for background processing ---
    ext = os.path.splitext(file.filename)[1] or ".jpg"
    temp_path = os.path.join(UPLOAD_DIR, f"{job_id}{ext}")

    async with aiofiles.open(temp_path, "wb") as f:
        await f.write(file_bytes)

    background_tasks.add_task(run_ai_pipeline, job_id, temp_path)

    return {
        "job_id": job_id,
        "squad_ref": squad_ref,
        "payment_amount": PAYMENT_AMOUNT,
        "currency": CURRENCY,
        "cached": job.get("cached", False),
        "status": "processing",
        "message": "Certificate received. Processing started.",
        "poll_url": f"/result/{job_id}",
    }


@app.get("/result/{job_id}")
def result(job_id: str):
    try:
        uuid.UUID(job_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Verification job not found")

    try:
        verification = get_verification_result(job_id)
    except Exception as exc:
        logger.error(f"Could not fetch verification result {job_id}: {exc}")
        raise HTTPException(
            status_code=503,
            detail="Verification database is temporarily unavailable"
        )

    if verification is None:
        raise HTTPException(status_code=404, detail="Verification job not found")
    return format_verification_result(verification)


def format_verification_result(verification: dict) -> dict:
    return {
        "id": verification.get("id"),
        "file_hash": verification.get("file_hash"),
        "trust_score": verification.get("trust_score"),
        "verdict": verification.get("verdict"),
        "flags": verification.get("flags", []),
        "layers_analyzed": verification.get("layers_analyzed", []),
        "confidence": verification.get("confidence"),
        "status": verification.get("status"),
    }


# ─────────────────────────────────────────
# AI PIPELINE
# ─────────────────────────────────────────

async def run_ai_pipeline(job_id: str, file_path: str):
    """
    Full 2-layer AI analysis pipeline.
    Layer 1: Visual forensics (ELA + metadata + visual)
    Layer 2: Content validation (OCR + institution matching)
    """
    logger.info(f"AI pipeline started → job: {job_id}")

    try:
        layers_run = []
        all_flags = []
        layer_scores = {}

        # ── LAYER 1: Visual Forensics ──────────────────────────────
        try:
            ela_result = perform_ela(file_path)
            meta_result = check_metadata_consistency(file_path)
            visual_result = analyze_visual_consistency(file_path)

            visual_trust = calculate_visual_trust_score(
                ela_result, meta_result, visual_result
            )

            layer_scores["visual"] = visual_trust["trust_score"]
            all_flags.extend(visual_trust["flags"])
            layers_run.append("visual_forensics")

            logger.info(
                f"Layer 1 done → visual score: {layer_scores['visual']}"
            )

        except Exception as e:
            logger.error(f"Layer 1 error: {e}")
            all_flags.append("Visual analysis could not complete")

        # ── LAYER 2: Content Validation ────────────────────────────
        try:
            ocr_result = extract_text(file_path)

            if ocr_result.get("success"):
                content_result = validate_certificate_content(
                    ocr_result["text"]
                )

                layer_scores["content"] = content_result["content_score"]
                all_flags.extend(content_result["flags"])
                layers_run.append("content_validation")

                logger.info(
                    f"Layer 2 done → content score: {layer_scores['content']}"
                    f" | institution: {content_result['detected_institution']}"
                )
            else:
                content_result = validate_certificate_content("")
                layer_scores["content"] = content_result["content_score"]
                all_flags.extend(content_result["flags"])
                layers_run.append("content_validation")
                all_flags.append(
                    f"OCR failed: {ocr_result.get('error', 'unknown')}"
                )

        except Exception as e:
            logger.error(f"Layer 2 error: {e}")
            all_flags.append("Content extraction could not complete")

        # ── AGGREGATE FINAL SCORE ──────────────────────────────────
        final_score = aggregate_scores(layer_scores)
        verdict = determine_verdict(final_score)
        confidence = (
            "HIGH" if len(layers_run) == 2
            else "MEDIUM" if len(layers_run) == 1
            else "LOW"
        )

        # Remove duplicate flags
        unique_flags = list(dict.fromkeys(all_flags))

        # ── STORE RESULT ───────────────────────────────────────────
        update_verification_result(job_id, {
            "trust_score": final_score,
            "verdict": verdict,
            "flags": unique_flags,
            "layers_analyzed": layers_run,
            "confidence": confidence
        })

        logger.info(
            f"Job {job_id} complete → "
            f"score: {final_score} | verdict: {verdict}"
        )

    except Exception as e:
        logger.error(f"Pipeline crashed for job {job_id}: {e}")
        update_verification_result(job_id, {
            "trust_score": 0,
            "verdict": "PROCESSING_ERROR",
            "flags": [f"System error: {str(e)}"],
            "layers_analyzed": [],
            "confidence": "LOW"
        })

    finally:
        # Always clean up temp file (no matter what)
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Temp file removed: {file_path}")
        except Exception as e:
            logger.warning(f"Could not remove temp file: {e}")


def aggregate_scores(layer_scores: dict) -> int:
    """
    Weighted score aggregation.
    Visual forensics = 60% weight
    Content validation = 40% weight
    """
    if not layer_scores:
        return 0

    weights = {"visual": 0.60, "content": 0.40}
    weighted_sum = 0
    total_weight = 0

    for layer, score in layer_scores.items():
        w = weights.get(layer, 0.5)
        weighted_sum += score * w
        total_weight += w

    final_score = round(weighted_sum / total_weight) if total_weight > 0 else 0

    if layer_scores.get("content", 100) <= 20:
        final_score = min(final_score, 50)

    return final_score


def determine_verdict(score: int) -> str:
    if score >= 75:
        return "LIKELY AUTHENTIC"
    elif score >= 50:
        return "REQUIRES MANUAL REVIEW"
    elif score >= 25:
        return "SUSPICIOUS"
    else:
        return "LIKELY FORGED"


if __name__ == "__main__":
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
