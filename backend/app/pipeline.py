# app/pipeline.py
# THIS IS YOUR INTERFACE WITH DIVINE
# Divine calls trigger_ai_pipeline(verification_id) after payment confirmed
# That is ALL he needs to know about your code

import logging
import os

try:
    from .ocr import extract_text
    from .ela import (
        perform_ela,
        check_metadata_consistency,
        analyze_visual_consistency,
    )
    from .scorer import calculate_visual_trust_score
    from .content_validator import validate_certificate_content
    from .database import update_verification_result, get_supabase
except ImportError:
    from app.ocr import extract_text
    from app.ela import (
        perform_ela,
        check_metadata_consistency,
        analyze_visual_consistency,
    )
    from app.scorer import calculate_visual_trust_score
    from app.content_validator import validate_certificate_content
    from app.database import update_verification_result, get_supabase

logger = logging.getLogger(__name__)


async def trigger_ai_pipeline(verification_id: str) -> None:
    """
    DIVINE CALLS THIS FUNCTION.
    
    Contract:
    - Input: verification_id (UUID string from verifications table)
    - Divine must have already:
        1. Confirmed payment in Supabase (payments.status = 'confirmed')
        2. Stored the file in Supabase Storage at path: certificates/{verification_id}
    - This function:
        1. Reads file_url from Supabase using verification_id
        2. Downloads the file
        3. Runs 2-layer AI pipeline
        4. Updates verifications table with results
        5. Sets status = 'COMPLETE' or 'FAILED'
    - Output: None (results written directly to Supabase)
    - Timeout: Must complete within 90 seconds
    """
    logger.info(f"AI pipeline triggered → verification_id: {verification_id}")

    try:
        # Step 1: Get file info from Supabase
        supabase = get_supabase()
        record = supabase.table("verifications")\
            .select("file_url, file_hash, status")\
            .eq("id", verification_id)\
            .single()\
            .execute()

        if not record.data:
            logger.error(f"Verification record not found: {verification_id}")
            return

        file_url = record.data.get("file_url")
        if not file_url:
            logger.error(f"No file_url for verification: {verification_id}")
            _mark_failed(verification_id, "No file found for this verification")
            return

        # Step 2: Download file to temp location
        file_path = await _download_file(file_url, verification_id)
        if not file_path:
            _mark_failed(verification_id, "Could not download certificate file")
            return

        # Step 3: Run AI pipeline
        await _run_pipeline(verification_id, file_path)

    except Exception as e:
        logger.error(f"Pipeline crashed → {verification_id}: {e}")
        _mark_failed(verification_id, f"System error: {str(e)}")


async def _download_file(file_url: str, verification_id: str) -> str:
    """Download file from Supabase Storage to /tmp"""
    import httpx

    try:
        tmp_dir = "/tmp/verifyng"
        os.makedirs(tmp_dir, exist_ok=True)

        # Determine extension from URL
        ext = os.path.splitext(file_url.split("?")[0])[1] or ".jpg"
        tmp_path = f"{tmp_dir}/{verification_id}{ext}"

        async with httpx.AsyncClient() as client:
            response = await client.get(file_url, timeout=30.0)
            response.raise_for_status()

            with open(tmp_path, "wb") as f:
                f.write(response.content)

        logger.info(f"File downloaded: {tmp_path}")
        return tmp_path

    except Exception as e:
        logger.error(f"File download failed: {e}")
        return None


async def _run_pipeline(verification_id: str, file_path: str) -> None:
    """Core AI processing — 2 layers"""
    layers_run = []
    all_flags = []
    layer_scores = {}

    try:
        # ── LAYER 1: Visual Forensics ──────────────────────────────
        try:
            ela = perform_ela(file_path)
            meta = check_metadata_consistency(file_path)
            visual = analyze_visual_consistency(file_path)
            visual_trust = calculate_visual_trust_score(ela, meta, visual)

            layer_scores["visual"] = visual_trust["trust_score"]
            all_flags.extend(visual_trust["flags"])
            layers_run.append("visual_forensics")

            logger.info(f"Layer 1 done → score: {layer_scores['visual']}")

        except Exception as e:
            logger.error(f"Layer 1 failed: {e}")
            all_flags.append("Visual analysis could not complete")

        # ── LAYER 2: Content Validation ────────────────────────────
        try:
            ocr = extract_text(file_path)

            if ocr.get("success"):
                content = validate_certificate_content(ocr["text"])
                layer_scores["content"] = content["content_score"]
                all_flags.extend(content["flags"])
                layers_run.append("content_validation")

                logger.info(
                    f"Layer 2 done → score: {layer_scores['content']} | "
                    f"institution: {content.get('detected_institution')}"
                )
            else:
                all_flags.append(f"OCR failed: {ocr.get('error', 'unknown')}")

        except Exception as e:
            logger.error(f"Layer 2 failed: {e}")
            all_flags.append("Content extraction could not complete")

        # ── AGGREGATE ──────────────────────────────────────────────
        final_score = _aggregate_scores(layer_scores)
        verdict = _determine_verdict(final_score)
        confidence = (
            "HIGH" if len(layers_run) == 2
            else "MEDIUM" if len(layers_run) == 1
            else "LOW"
        )

        # ── STORE RESULT ───────────────────────────────────────────
        update_verification_result(verification_id, {
            "trust_score": final_score,
            "verdict": verdict,
            "flags": list(dict.fromkeys(all_flags)),
            "layers_analyzed": layers_run,
            "confidence": confidence
        })

        logger.info(
            f"Pipeline complete → {verification_id} | "
            f"score: {final_score} | verdict: {verdict}"
        )

    finally:
        # Always clean up temp file
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Temp file removed: {file_path}")
        except Exception as e:
            logger.warning(f"Cleanup failed: {e}")


def _mark_failed(verification_id: str, reason: str) -> None:
    """Mark verification as failed in Supabase"""
    try:
        update_verification_result(verification_id, {
            "trust_score": None,
            "verdict": "FAILED",
            "flags": [reason],
            "layers_analyzed": [],
            "confidence": "LOW",
            "status": "FAILED"
        })
        logger.info(f"Marked as FAILED → {verification_id}: {reason}")
    except Exception as e:
        logger.error(f"Could not mark as failed: {e}")


def _aggregate_scores(layer_scores: dict) -> int:
    if not layer_scores:
        return 0
    weights = {"visual": 0.60, "content": 0.40}
    weighted_sum = sum(
        layer_scores[k] * weights.get(k, 0.5)
        for k in layer_scores
    )
    total_weight = sum(weights.get(k, 0.5) for k in layer_scores)
    return round(weighted_sum / total_weight) if total_weight else 0


def _determine_verdict(score: int) -> str:
    if score >= 75:   return "LIKELY AUTHENTIC"
    if score >= 50:   return "REQUIRES MANUAL REVIEW"
    if score >= 25:   return "SUSPICIOUS"
    return "LIKELY FORGED"
