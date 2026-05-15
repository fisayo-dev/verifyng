import logging
import os
import tempfile
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, HTTPException, UploadFile

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
router = APIRouter()

DEFAULT_SUPABASE_STORAGE_BUCKET = os.getenv("SUPABASE_STORAGE_BUCKET", "certificates")


@router.post("/api/verify")
async def verify_certificate(file: UploadFile = File(...)):
    """Upload certificate file, create verification and payment, then return checkout details."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="File upload is required")

    temp_dir = Path(tempfile.gettempdir()) / "verifyng"
    temp_dir.mkdir(parents=True, exist_ok=True)
    temp_file_path = str(temp_dir / f"{uuid.uuid4()}_{Path(file.filename).name}")

    try:
        contents = await file.read()
        with open(temp_file_path, "wb") as handle:
            handle.write(contents)
    except Exception as exc:
        logger.error("Failed to save uploaded file: %s", exc)
        raise HTTPException(status_code=500, detail="Unable to save uploaded file")

    try:
        verification = create_verification(temp_file_path, file.filename, temp_file_path)
        job_id = verification["job_id"]
    except Exception as exc:
        logger.error("Failed to create verification job: %s", exc)
        raise HTTPException(status_code=500, detail="Unable to create verification job")

    checkout_url = ""

    if os.getenv("SQUAD_API_KEY"):
        try:
            from .payments import initiate_payment

            payment_response = await initiate_payment(
                amount=50000,
                email="customer@example.com",
                verification_id=job_id,
            )
            checkout_url = (
                payment_response.get("checkout_url")
                or payment_response.get("data", {}).get("checkout_url", "")
                or ""
            )
        except HTTPException:
            raise
        except Exception as exc:
            logger.error("Failed to initiate payment: %s", exc)
            raise HTTPException(status_code=500, detail="Unable to initiate payment")

    return {
        "job_id": job_id,
        "checkout_url": checkout_url,
        "status": "PENDING_PAYMENT",
        "poll_url": f"https://olatunjitobi-verifyng-api.hf.space/api/result/{job_id}",
    }
    

def create_verification(file_path: str, file_name: str, temp_file_path: str) -> dict:
    """Create verification metadata for the uploaded file."""
    return create_verification_job(file_name, temp_file_path)


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
    storage_path = f"{verification_id}/{file_path.name}"

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

    signed_url = _create_signed_storage_url(bucket, storage_path)
    if signed_url:
        return signed_url

    public_url = bucket.get_public_url(storage_path)
    if not public_url:
        raise RuntimeError("Unable to generate public URL for uploaded file")

    return public_url


def _create_signed_storage_url(bucket, storage_path: str) -> Optional[str]:
    """Prefer a signed URL so private Supabase buckets can be downloaded."""
    try:
        response = bucket.create_signed_url(storage_path, 3600)
    except Exception as exc:
        logger.warning("Could not create signed Supabase URL: %s", exc)
        return None

    if isinstance(response, dict):
        signed_url = (
            response.get("signedURL")
            or response.get("signedUrl")
            or response.get("signed_url")
        )
        return _absolute_storage_url(signed_url)

    signed_url = (
        getattr(response, "signedURL", None)
        or getattr(response, "signedUrl", None)
        or getattr(response, "signed_url", None)
    )
    return _absolute_storage_url(signed_url)


def _absolute_storage_url(url: Optional[str]) -> Optional[str]:
    if not url:
        return None
    if url.startswith("http://") or url.startswith("https://"):
        return url
    if url.startswith("/"):
        supabase_url = os.getenv("SUPABASE_URL", "").rstrip("/")
        if supabase_url:
            return f"{supabase_url}{url}"
    return url


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
