import logging
import os
from pathlib import Path
from typing import Optional

from .database import (

    create_payment_record,
    create_verification_job,
    get_supabase,
    get_verification_result,
    has_supabase_config,
    _LOCAL_VERIFICATIONS,
)
from .pipeline import trigger_ai_pipeline

logger = logging.getLogger(__name__)

DEFAULT_SUPABASE_STORAGE_BUCKET = os.getenv("SUPABASE_STORAGE_BUCKET", "certificates")


def create_verification(file_hash: str, file_name: str, temp_file_path: str) -> dict:
    """Create a verification job with temporary file path."""
    return create_verification_job(file_hash, file_name, temp_file_path)


def initialize_payment(verification_id: str, squad_ref: str) -> dict:
    """Reserve a payment for the verification job.

    This is a placeholder for the payment initialization step.
    The actual payment flow will be implemented later.
    """
    logger.info(
        "Initializing payment for verification_id=%s squad_ref=%s",
        verification_id,
        squad_ref,
    )

    return create_payment_record(squad_ref=squad_ref, verification_id=verification_id)


async def verify_payment(
    verification_id: str,
    file_path: str,
    squad_ref: str,
) -> dict:
    """Upload the file, update verification, then trigger AI pipeline."""
    bucket_name = DEFAULT_SUPABASE_STORAGE_BUCKET
    file_path_obj = Path(file_path)

    if not verification_id:
        raise ValueError("verification_id is required")
    if not squad_ref:
        raise ValueError("squad_ref is required")
    if not file_path_obj.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    logger.info(
        "Processing verification for verification_id=%s squad_ref=%s",
        verification_id,
        squad_ref,
    )

    file_url = _upload_file_to_storage(
        file_path=file_path_obj,
        verification_id=verification_id,
        bucket_name=bucket_name,
    )

    _update_verification_record(
        verification_id=verification_id,
        file_url=file_url,
    )

    # Clean up temporary file
    try:
        os.remove(file_path)
        logger.info(f"Cleaned up temporary file: {file_path}")
    except Exception as e:
        logger.warning(f"Failed to clean up temporary file {file_path}: {e}")

    logger.info(
        "File uploaded and verification updated. Starting AI pipeline for %s",
        verification_id,
    )

    await trigger_ai_pipeline(verification_id)

    return {
        "verification_id": verification_id,
        "status": "PROCESSING",
        "file_url": file_url,
    }


def _upload_file_to_storage(
    file_path: Path,
    verification_id: str,
    bucket_name: str,
) -> str:
    if not has_supabase_config():
        logger.warning(
            "Supabase config not present, using local file URL for verification %s",
            verification_id,
        )
        return f"file://{file_path.resolve()}"

    supabase = get_supabase()
    bucket = supabase.storage.from_(bucket_name)
    storage_path = verification_id

    logger.info(
        "Uploading file %s to Supabase storage bucket=%s path=%s",
        file_path,
        bucket_name,
        storage_path,
    )

    upload_response = bucket.upload(storage_path, str(file_path))
    if not upload_response or getattr(upload_response, "error", None):
        error_detail = getattr(upload_response, "error", None)
        raise RuntimeError(
            f"Supabase storage upload failed: {error_detail}"
        )

    public_url = bucket.get_public_url(storage_path)
    if not public_url:
        raise RuntimeError("Unable to generate public URL for uploaded file")

    return public_url


def _update_verification_record(verification_id: str, file_url: str) -> dict:
    if has_supabase_config():
        supabase = get_supabase()
        updated = supabase.table("verifications").update({
            "file_url": file_url,
            "status": "PROCESSING",
        }).eq("id", verification_id).execute()
        return updated.data[0] if updated.data else {}

    verification = _LOCAL_VERIFICATIONS.get(verification_id)
    if not verification:
        raise RuntimeError(
            f"Local verification record not found: {verification_id}"
        )

    verification.update({
        "file_url": file_url,
        "status": "PROCESSING",
    })
    return verification
