import logging
import uuid

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .database import get_verification_result
from .pipeline import trigger_ai_pipeline

logger = logging.getLogger(__name__)

app = FastAPI(
    title="VerifyNG API",
    description="AI-powered certificate verification",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "version": "1.0.0",
        "service": "VerifyNG",
    }


@app.post("/verify")
async def verify_stub():
    raise HTTPException(
        status_code=501,
        detail=(
            "Divine owns the full /verify implementation. Call /trigger/{job_id} "
            "after payment and upload are complete."
        ),
    )


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
            detail="Verification database is temporarily unavailable",
        )

    if verification is None:
        raise HTTPException(status_code=404, detail="Verification job not found")
    return format_verification_result(verification)


@app.post("/trigger/{job_id}")
def trigger_pipeline_demo(job_id: str, background_tasks: BackgroundTasks):
    try:
        uuid.UUID(job_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Verification job not found")

    background_tasks.add_task(trigger_ai_pipeline, job_id)
    return {
        "job_id": job_id,
        "status": "PROCESSING",
        "message": "AI pipeline queued for demo trigger.",
    }


def format_verification_result(verification: dict) -> dict:
    status = verification.get("status")

    if status in {"PENDING_PAYMENT", "PAID", "PROCESSING"}:
        return {"status": status}

    if status == "FAILED":
        return {
            "status": "FAILED",
            "flags": verification.get("flags", []),
        }

    return {
        "id": verification.get("id"),
        "status": status,
        "trust_score": verification.get("trust_score"),
        "verdict": verification.get("verdict"),
        "flags": verification.get("flags", []),
        "confidence": verification.get("confidence"),
        "layers_run": verification.get("layers_run", []),
    }
