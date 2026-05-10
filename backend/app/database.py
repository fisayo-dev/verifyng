# app/database.py

from supabase import create_client, Client
from dotenv import load_dotenv
import os

load_dotenv()

def get_supabase() -> Client:
    """Get Supabase client — called fresh each request (stateless)"""
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    
    if not url or not key:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set")
    
    return create_client(url, key)


def create_verification_job(file_hash: str, file_name: str) -> dict:
    """Create a new verification job in pending state"""
    supabase = get_supabase()
    
    # Check if this file was already verified (deduplication)
    existing = supabase.table("verifications")\
        .select("*")\
        .eq("file_hash", file_hash)\
        .execute()
    
    if existing.data:
        return {
            "job_id": existing.data[0]["id"],
            "cached": True,
            "data": existing.data[0]
        }
    
    # Create new job
    result = supabase.table("verifications").insert({
        "file_hash": file_hash,
        "file_name": file_name,
        "status": "pending"
    }).execute()
    
    return {
        "job_id": result.data[0]["id"],
        "cached": False,
        "data": result.data[0]
    }


def update_verification_result(job_id: str, result: dict) -> dict:
    """Store AI analysis result"""
    supabase = get_supabase()
    
    updated = supabase.table("verifications").update({
        "trust_score": result.get("trust_score"),
        "verdict": result.get("verdict"),
        "flags": result.get("flags", []),
        "layers_analyzed": result.get("layers_analyzed", []),
        "confidence": result.get("confidence", "MEDIUM"),
        "status": "completed",
        "updated_at": "now()"
    }).eq("id", job_id).execute()
    
    return updated.data[0] if updated.data else {}


def get_verification_result(job_id: str) -> dict:
    """Fetch verification result by job ID"""
    supabase = get_supabase()
    
    result = supabase.table("verifications")\
        .select("*, payments(*)")\
        .eq("id", job_id)\
        .single()\
        .execute()
    
    return result.data if result.data else None


def create_payment_record(squad_ref: str, verification_id: str) -> dict:
    """Create payment record linked to verification job"""
    supabase = get_supabase()
    
    result = supabase.table("payments").insert({
        "squad_ref": squad_ref,
        "verification_id": verification_id,
        "status": "pending"
    }).execute()
    
    return result.data[0] if result.data else {}


def confirm_payment(squad_ref: str) -> dict:
    """Mark payment as confirmed — triggers AI pipeline"""
    supabase = get_supabase()
    
    result = supabase.table("payments").update({
        "status": "confirmed",
        "updated_at": "now()"
    }).eq("squad_ref", squad_ref).execute()
    
    return result.data[0] if result.data else {}


def get_institution_formats() -> list:
    """Fetch all known institution formats for validation"""
    supabase = get_supabase()
    
    result = supabase.table("institution_formats")\
        .select("*")\
        .execute()
    
    return result.data if result.data else []
