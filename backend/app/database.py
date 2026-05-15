# app/database.py

import os
import uuid
from pathlib import Path

from dotenv import load_dotenv
from postgrest.exceptions import APIError
from supabase import Client, create_client

BACKEND_ENV_PATH = str(Path(__file__).resolve().parents[1] / ".env")

load_dotenv()
load_dotenv(BACKEND_ENV_PATH)

_LOCAL_VERIFICATIONS = {}
_LOCAL_PAYMENTS = {}


def has_supabase_config() -> bool:
    return bool(os.environ.get("SUPABASE_URL") and get_supabase_key())


def get_supabase_key() -> str:
    return (
        os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        or os.environ.get("SUPABASE_SERVICE_KEY")
        or os.environ.get("SUPABASE_KEY")
    )


def reset_local_store():
    """Reset the in-memory fallback store. Intended for tests."""
    _LOCAL_VERIFICATIONS.clear()
    _LOCAL_PAYMENTS.clear()


def get_supabase() -> Client:
    """Get Supabase client, called fresh each request."""
    url = os.environ.get("SUPABASE_URL")
    key = get_supabase_key()

    if not url or not key:
        raise ValueError(
            "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY or SUPABASE_KEY must be set"
        )

    return create_client(url, key)


def create_verification_job(file_name: str, temp_file_path: str) -> dict:
    """Create a new verification job in pending state."""
    file_hash = _build_upload_identity(file_name, temp_file_path)

    if not has_supabase_config():
        job_id = str(uuid.uuid4())
        job = {
            "id": job_id,
            "file_hash": file_hash,
            "file_name": file_name,
            "temp_file_path": temp_file_path,
            "status": "pending",
        }
        _LOCAL_VERIFICATIONS[job_id] = job
        return {
            "job_id": job_id,
            "cached": False,
            "data": job,
        }

    supabase = get_supabase()

    result = supabase.table("verifications").insert({
        "file_hash": file_hash,
        "file_name": file_name,
        "temp_file_path": temp_file_path,
        "status": "pending",
    }).execute()

    return {
        "job_id": result.data[0]["id"],
        "cached": False,
        "data": result.data[0],
    }


def _build_upload_identity(file_name: str, temp_file_path: str) -> str:
    """Create a per-upload identity without reusing the display filename."""
    upload_token = Path(temp_file_path).name or str(uuid.uuid4())
    return f"{file_name}:{upload_token}"


def update_verification_result(verification_id: str, result: dict) -> dict:
    """
    Update verification record with AI pipeline results.
    Called by trigger_ai_pipeline() after analysis completes.

    Status values (from Divine's PRD):
    PENDING_PAYMENT | PAID | PROCESSING | COMPLETE | FAILED
    """
    status = result.get("status", "COMPLETE")

    if result.get("verdict") == "FAILED":
        status = "FAILED"
    elif result.get("trust_score") is not None:
        status = "COMPLETE"

    import datetime

    update_data = {
        "trust_score": result.get("trust_score"),
        "verdict": result.get("verdict"),
        "flags": result.get("flags", []),
        "layers_run": result.get("layers_analyzed", []),
        "confidence": result.get("confidence", "LOW"),
        "status": status,
        "completed_at": datetime.datetime.now(datetime.UTC).isoformat(),
    }

    if not has_supabase_config():
        existing = _LOCAL_VERIFICATIONS.get(verification_id)
        if not existing:
            return {}

        existing.update(update_data)
        return existing

    supabase = get_supabase()

    updated = supabase.table("verifications").update(update_data)\
        .eq("id", verification_id)\
        .execute()

    return updated.data[0] if updated.data else {}


def get_verification_result(job_id: str) -> dict:
    """Fetch verification result by job ID."""
    if not has_supabase_config():
        verification = _LOCAL_VERIFICATIONS.get(job_id)
        if not verification:
            return None

        payments = [
            payment for payment in _LOCAL_PAYMENTS.values()
            if payment["verification_id"] == job_id
        ]
        return {
            **verification,
            "payments": payments,
        }

    supabase = get_supabase()

    try:
        result = supabase.table("verifications")\
            .select("*, payments(*)")\
            .eq("id", job_id)\
            .single()\
            .execute()
    except APIError as exc:
        if is_missing_single_row_error(exc):
            return None
        raise

    return result.data if result.data else None


def is_missing_single_row_error(exc: Exception) -> bool:
    """Return True when Supabase/PostgREST reports zero rows for .single()."""
    return (
        isinstance(exc, APIError)
        and getattr(exc, "code", None) == "PGRST116"
    )


def create_payment_record(squad_ref: str, verification_id: str) -> dict:
    """Create payment record linked to verification job."""
    if not has_supabase_config():
        if squad_ref in _LOCAL_PAYMENTS:
            return _LOCAL_PAYMENTS[squad_ref]

        payment = {
            "squad_ref": squad_ref,
            "verification_id": verification_id,
            "status": "pending",
        }
        _LOCAL_PAYMENTS[squad_ref] = payment
        return payment

    supabase = get_supabase()

    existing = supabase.table("payments")\
        .select("*")\
        .eq("squad_ref", squad_ref)\
        .execute()

    if existing.data:
        return existing.data[0]

    result = supabase.table("payments").insert({
        "squad_ref": squad_ref,
        "verification_id": verification_id,
        "status": "pending",
    }).execute()

    return result.data[0] if result.data else {}


def confirm_payment(squad_ref: str) -> dict:
    """Mark payment as confirmed after successful Squad verification."""
    if not has_supabase_config():
        payment = _LOCAL_PAYMENTS.get(squad_ref)
        if not payment:
            return None

        payment["status"] = "confirmed"
        return payment

    supabase = get_supabase()

    updated = supabase.table("payments").update({
        "status": "confirmed",
    }).eq("squad_ref", squad_ref).execute()

    return updated.data[0] if updated.data else None


def get_payment_by_squad_ref(squad_ref: str) -> dict:
    """Fetch payment record by squad_ref."""
    if not has_supabase_config():
        payment = _LOCAL_PAYMENTS.get(squad_ref)
        if not payment:
            return None
        return payment

    supabase = get_supabase()

    result = supabase.table("payments")\
        .select("*")\
        .eq("squad_ref", squad_ref)\
        .single()\
        .execute()

    return result.data if result.data else None


def get_institution_formats() -> list:
    """Fetch all known institution formats for validation."""
    if not has_supabase_config():
        return []

    supabase = get_supabase()

    result = supabase.table("institution_formats")\
        .select("*")\
        .execute()

    return result.data if result.data else []
