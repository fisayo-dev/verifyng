from fastapi import APIRouter, HTTPException

from .database import get_verification_result

router = APIRouter()


@router.get("/ws/check_file_status/{jobid}")
def check_file_status(jobid: str):
    """Poll for file verification status and AI pipeline results."""
    result = get_verification_result(jobid)
    if not result:
        raise HTTPException(status_code=404, detail="Job not found")

    return {
        "id": result.get("id"),
        "status": result.get("status"),
        "trust_score": result.get("trust_score"),
        "verdict": result.get("verdict"),
        "confidence": result.get("confidence"),
        "flags": result.get("flags", []),
        "layers_run": result.get("layers_run", []),
    }