import logging
import os
import uuid

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request

from .database import get_supabase, is_missing_single_row_error
from .pipeline import trigger_ai_pipeline

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/api/result/{verification_id}")
def get_result(verification_id: str):
    """Fisayo polls this every 3 seconds."""
    _raise_not_found_if_invalid_uuid(verification_id)
    supabase = get_supabase()

    try:
        record = supabase.table("verifications")\
            .select("*")\
            .eq("id", verification_id)\
            .single()\
            .execute()
    except Exception as exc:
        if is_missing_single_row_error(exc):
            raise HTTPException(status_code=404, detail={
                "error": "NOT_FOUND",
                "message": "Verification ID not found",
            })
        raise

    if not record.data:
        raise HTTPException(status_code=404, detail={
            "error": "NOT_FOUND",
            "message": "Verification ID not found",
        })

    data = record.data
    status = data.get("status")

    if status == "FAILED":
        return {
            "verification_id": verification_id,
            "status": "FAILED",
            "message": "Verification failed. Please contact support.",
            "refund_eligible": True,
        }

    if status != "COMPLETE":
        return {
            "verification_id": verification_id,
            "status": status,
            "message": {
                "PENDING_PAYMENT": "Awaiting payment confirmation",
                "PAID": "Payment confirmed. Waiting for analysis...",
                "PROCESSING": "AI is analyzing your certificate...",
                "FAILED": "Verification failed. Please contact support.",
            }.get(status, "Processing..."),
        }

    return {
        "verification_id": verification_id,
        "status": "COMPLETE",
        "trust_score": data.get("trust_score"),
        "verdict": data.get("verdict"),
        "flags": data.get("flags", []),
        "confidence": data.get("confidence"),
        "layers_run": data.get("layers_run", []),
        "report_url": data.get("report_url"),
    }


@router.get("/api/report/{verification_id}")
def get_report(verification_id: str):
    """Return the generated PDF report URL after verification completes."""
    _raise_not_found_if_invalid_uuid(verification_id)
    supabase = get_supabase()

    record = supabase.table("verifications")\
        .select("id, status, report_url")\
        .eq("id", verification_id)\
        .single()\
        .execute()

    if not record.data:
        raise HTTPException(status_code=404, detail={
            "error": "NOT_FOUND",
            "message": "Verification ID not found",
        })

    if record.data.get("status") != "COMPLETE" or not record.data.get("report_url"):
        raise HTTPException(status_code=409, detail={
            "error": "REPORT_NOT_READY",
            "message": "Report is not available until verification is complete.",
        })

    return {
        "verification_id": verification_id,
        "report_url": record.data["report_url"],
    }


@router.post("/api/trigger/{verification_id}")
async def manual_trigger(
    verification_id: str,
    background_tasks: BackgroundTasks,
    request: Request,
):
    """
    Testing only: bypasses Squad payment.

    This endpoint is intentionally guarded because Divine owns the real
    upload/payment/webhook path.
    """
    expected_api_key = os.getenv("API_KEY", "")
    provided_api_key = request.headers.get("X-API-Key", "")
    if not expected_api_key or provided_api_key != expected_api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")

    _raise_not_found_if_invalid_uuid(verification_id, message="Job not found")

    supabase = get_supabase()
    record = supabase.table("verifications")\
        .select("id, status, file_url")\
        .eq("id", verification_id)\
        .single()\
        .execute()

    if not record.data:
        raise HTTPException(status_code=404, detail="Job not found")

    if not record.data.get("file_url"):
        raise HTTPException(
            status_code=400,
            detail="file_url is not set. Divine must upload the file first.",
        )

    supabase.table("verifications").update({
        "status": "PROCESSING",
    }).eq("id", verification_id).execute()

    background_tasks.add_task(trigger_ai_pipeline, verification_id)

    return {
        "status": "triggered",
        "verification_id": verification_id,
        "poll_url": f"/api/result/{verification_id}",
    }


def _raise_not_found_if_invalid_uuid(
    verification_id: str,
    message: str = "Verification ID not found",
) -> None:
    try:
        uuid.UUID(verification_id)
    except ValueError:
        raise HTTPException(status_code=404, detail={
            "error": "NOT_FOUND",
            "message": message,
        })
