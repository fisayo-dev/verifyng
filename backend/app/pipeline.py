# app/pipeline.py
# THIS IS YOUR INTERFACE WITH DIVINE
# Divine calls trigger_ai_pipeline(verification_id) after payment confirmed
# That is ALL he needs to know about your code

import logging
import os
import asyncio

try:
    from .ocr import extract_text
    from .ela import (
        perform_ela,
        check_metadata_consistency,
        analyze_visual_consistency,
    )
    from .scorer import calculate_visual_trust_score
    from .content_validator import validate_certificate_content
    from .ai_depth import build_ai_evidence_report, score_template_match
    from .ml_model import classify_certificate
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
    from app.ai_depth import build_ai_evidence_report, score_template_match
    from app.ml_model import classify_certificate
    from app.database import update_verification_result, get_supabase

logger = logging.getLogger(__name__)


async def trigger_ai_pipeline(verification_id: str) -> None:
    """
    DIVINE CALLS THIS FUNCTION. Wrapped with a 90-second timeout.

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
    logger.info(f"AI pipeline triggered -> verification_id: {verification_id}")

    try:
        await asyncio.wait_for(
            _run_pipeline_with_download(verification_id),
            timeout=90.0,
        )
    except asyncio.TimeoutError:
        logger.error(f"Pipeline timeout -> {verification_id}")
        _mark_failed(verification_id, "Analysis timed out. Please re-submit.")
    except Exception as e:
        logger.error(f"Pipeline error -> {verification_id}: {e}")
        _mark_failed(verification_id, f"System error: {str(e)}")


async def _run_pipeline_with_download(verification_id: str) -> None:
    """Download file from Supabase Storage, then run the AI pipeline."""
    import httpx

    supabase = get_supabase()

    try:
        record = supabase.table("verifications")\
            .select("id, file_url, status")\
            .eq("id", verification_id)\
            .single()\
            .execute()
    except Exception as e:
        logger.error(f"Supabase read failed: {e}")
        _mark_failed(verification_id, "Database read error")
        return

    if not record.data:
        logger.error(f"No verification record found: {verification_id}")
        _mark_failed(verification_id, "Verification record not found")
        return

    if record.data.get("status") == "COMPLETE":
        logger.info(f"Already COMPLETE, skipping pipeline: {verification_id}")
        return

    file_url = record.data.get("file_url")
    if not file_url:
        logger.error(f"No file_url for verification: {verification_id}")
        _mark_failed(
            verification_id,
            "No file URL found. Upload may have failed.",
        )
        return

    try:
        file_path = await _download_file(file_url, verification_id)
    except httpx.TimeoutException:
        logger.error(f"File download timed out: {file_url}")
        _mark_failed(verification_id, "File download timed out")
        return
    except Exception as e:
        logger.error(f"File download failed: {e}")
        _mark_failed(verification_id, "Could not download certificate file")
        return

    if not file_path:
        _mark_failed(verification_id, "Could not download certificate file")
        return

    await _run_pipeline(verification_id, file_path)


async def _download_file(file_url: str, verification_id: str) -> str:
    """Download file from Supabase Storage to /tmp"""
    import httpx

    if file_url.startswith("file://"):
        return file_url.replace("file:///", "", 1).replace("file://", "", 1)

    if "://" not in file_url:
        return file_url

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


async def _run_pipeline(verification_id: str, file_path: str) -> None:
    """Core AI processing — 2 layers"""
    layers_run = []
    all_flags = []
    layer_scores = {}
    failed_layers = 0
    ela = {}
    meta = {}
    ocr = {}
    template = {"template_score": 0, "field_scores": {}, "flags": []}

    try:
        # ── LAYER 1: Visual Forensics ──────────────────────────────
        try:
            ela = perform_ela(file_path)
            meta = check_metadata_consistency(file_path)
            visual = analyze_visual_consistency(file_path)
            visual_trust = calculate_visual_trust_score(ela, meta, visual)

            layer_scores["visual"] = visual_trust["trust_score"]
            layer_scores["extreme_visual_tamper"] = _has_extreme_visual_tamper(
                ela,
                visual_trust,
            )
            all_flags.extend(visual_trust["flags"])
            layers_run.append("visual_forensics")

            logger.info(f"Layer 1 done → score: {layer_scores['visual']}")

        except Exception as e:
            logger.error(f"Layer 1 failed: {e}")
            all_flags.append("Visual analysis could not complete")
            failed_layers += 1

        # ── LAYER 2: Content Validation ────────────────────────────
        try:
            ocr = extract_text(file_path)

            if ocr.get("success"):
                content = validate_certificate_content(ocr["text"])
                layer_scores["content"] = content["content_score"]
                all_flags.extend(content["flags"])
                layers_run.append("content_validation")

                template = score_template_match(
                    ocr["text"],
                    ocr_confidence=ocr.get("confidence", 0),
                )
                layer_scores["template"] = template["template_score"]
                all_flags.extend(template["flags"])
                layers_run.append("template_layout_matching")

                evidence = build_ai_evidence_report(
                    visual_score=layer_scores.get("visual", 0),
                    content_score=layer_scores["content"],
                    template_result=template,
                    ocr_result=ocr,
                )
                all_flags.extend(evidence["flags"])
                all_flags.append(_format_evidence_flag(evidence))

                logger.info(
                    f"Layer 2 done → score: {layer_scores['content']} | "
                    f"institution: {content.get('detected_institution')}"
                )
            else:
                content = validate_certificate_content("")
                layer_scores["content"] = content["content_score"]
                all_flags.extend(content["flags"])
                layers_run.append("content_validation")
                template = score_template_match("", ocr_confidence=0)
                layer_scores["template"] = template["template_score"]
                all_flags.extend(template["flags"])
                layers_run.append("template_layout_matching")
                all_flags.append(f"OCR failed: {ocr.get('error', 'unknown')}")
                failed_layers += 2

        except Exception as e:
            logger.error(f"Layer 2 failed: {e}")
            all_flags.append("Content extraction could not complete")
            failed_layers += 1

        # LAYER 4: Custom ML Authenticity Classifier
        try:
            ml_result = classify_certificate(_build_ml_features(
                layer_scores=layer_scores,
                ela=ela,
                meta=meta,
                ocr=ocr,
                template=template,
            ))
            layer_scores["ml"] = round(
                ml_result["ml_authenticity_probability"] * 100
            )
            layers_run.append("custom_ml_classifier")
            all_flags.append(
                "ML classifier: "
                f"prediction={ml_result['ml_prediction']}, "
                f"authenticity={ml_result['ml_authenticity_probability']}, "
                f"model={ml_result['ml_model']}"
            )
        except Exception as e:
            logger.error(f"Custom ML classifier failed: {e}")
            all_flags.append("Custom ML classifier could not complete")
            failed_layers += 1

        if not layers_run:
            update_verification_result(verification_id, {
                "trust_score": None,
                "verdict": "FAILED",
                "flags": list(dict.fromkeys(all_flags)) or [
                    "Pipeline could not analyze this file"
                ],
                "layers_analyzed": [],
                "confidence": "LOW",
                "status": "FAILED",
                "completed_at": "now()",
            })
            return

        # ── AGGREGATE ──────────────────────────────────────────────
        final_score = _aggregate_scores(layer_scores)
        verdict = _determine_verdict(final_score)
        successful_layers = sum(
            1
            for score in layer_scores.values()
            if isinstance(score, (int, float))
            and not isinstance(score, bool)
            and score >= 50
        )
        confidence = (
            "HIGH" if successful_layers >= 2
            else "MEDIUM" if successful_layers == 1
            else "LOW"
        )

        # ── STORE RESULT ───────────────────────────────────────────
        update_verification_result(verification_id, {
            "trust_score": final_score,
            "verdict": verdict,
            "flags": list(dict.fromkeys(all_flags)),
            "layers_analyzed": layers_run,
            "confidence": confidence,
            "completed_at": "now()",
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
            "status": "FAILED",
            "completed_at": "now()",
        })
        logger.info(f"Marked as FAILED → {verification_id}: {reason}")
    except Exception as e:
        logger.error(f"Could not mark as failed: {e}")


def _aggregate_scores(layer_scores: dict) -> int:
    if not layer_scores:
        return 0
    weights = {"visual": 0.35, "content": 0.25, "template": 0.20, "ml": 0.20}
    scored_layers = {
        key: value
        for key, value in layer_scores.items()
        if key in weights
    }
    weighted_sum = sum(
        scored_layers[k] * weights[k]
        for k in scored_layers
    )
    total_weight = sum(weights[k] for k in scored_layers)
    final_score = round(weighted_sum / total_weight) if total_weight else 0

    if layer_scores.get("content", 100) <= 20:
        final_score = min(final_score, 50)

    if layer_scores.get("template", 100) <= 35:
        final_score = min(final_score, 60)

    if layer_scores.get("ml", 100) <= 35:
        final_score = min(final_score, 65)

    if layer_scores.get("extreme_visual_tamper"):
        final_score = min(final_score, 49)
    elif (
        layer_scores.get("visual", 100) < 75
        and not _has_strong_waec_evidence(layer_scores)
    ):
        final_score = min(final_score, 74)

    return final_score


def _has_strong_waec_evidence(layer_scores: dict) -> bool:
    return (
        layer_scores.get("content", 0) >= 85
        and layer_scores.get("template", 0) >= 85
        and ("ml" not in layer_scores or layer_scores.get("ml", 0) >= 70)
        and layer_scores.get("visual", 0) >= 65
    )


def _build_ml_features(
    layer_scores: dict,
    ela: dict,
    meta: dict,
    ocr: dict,
    template: dict,
) -> dict:
    missing_field_count = sum(
        1
        for score in template.get("field_scores", {}).values()
        if score == 0
    )
    return {
        "visual_score": layer_scores.get("visual", 0),
        "content_score": layer_scores.get("content", 0),
        "template_score": layer_scores.get("template", 0),
        "ocr_confidence": ocr.get("confidence", 0) or 0,
        "ela_anomaly_score": ela.get("anomaly_score", 0) or 0,
        "metadata_suspicious": 1 if meta.get("suspicious") else 0,
        "missing_field_count": missing_field_count,
        "word_count": ocr.get("word_count", 0) or 0,
    }


def _has_extreme_visual_tamper(ela_result: dict, visual_trust: dict) -> bool:
    return (
        ela_result.get("risk_level") == "HIGH"
        or "Extreme pixel differences found in specific regions"
        in visual_trust.get("flags", [])
    )


def _format_evidence_flag(evidence: dict) -> str:
    scores = evidence["signal_scores"]
    return (
        "AI evidence: "
        f"visual={scores['visual_forensics']}, "
        f"content={scores['content_validation']}, "
        f"template={scores['template_match']}, "
        f"ocr={scores['ocr_confidence']} | "
        f"{evidence['judge_summary']}"
    )


def _determine_verdict(score: int) -> str:
    if score >= 75:   return "LIKELY AUTHENTIC"
    if score >= 50:   return "REQUIRES MANUAL REVIEW"
    if score >= 25:   return "SUSPICIOUS"
    return "LIKELY FORGED"
