import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import httpx

from backend.app.pipeline import (
    _aggregate_scores,
    _run_pipeline,
    _run_pipeline_with_download,
    trigger_ai_pipeline,
)


class PipelineTests(unittest.IsolatedAsyncioTestCase):
    def test_low_visual_score_caps_final_score_below_authentic(self):
        score = _aggregate_scores({
            "visual": 68,
            "content": 100,
        })

        self.assertLess(score, 75)

    def test_strong_waec_evidence_can_pass_with_moderate_scan_artifacts(self):
        score = _aggregate_scores({
            "visual": 70.3,
            "content": 90,
            "template": 90,
            "ml": 70,
        })

        self.assertGreaterEqual(score, 75)

    def test_extreme_visual_tamper_fails_even_with_strong_text_match(self):
        score = _aggregate_scores({
            "visual": 68.3,
            "content": 100,
            "template": 89,
            "extreme_visual_tamper": True,
        })

        self.assertLess(score, 50)

    def test_non_score_flags_do_not_change_weighted_average(self):
        with_flag = _aggregate_scores({
            "visual": 79.1,
            "content": 100,
            "template": 100,
            "extreme_visual_tamper": False,
        })
        without_flag = _aggregate_scores({
            "visual": 79.1,
            "content": 100,
            "template": 100,
        })

        self.assertEqual(with_flag, without_flag)

    async def test_ocr_failure_contributes_low_content_score(self):
        captured = {}

        def capture_result(job_id, result):
            captured.update(result)
            return result

        with patch("backend.app.pipeline.perform_ela", return_value={
            "success": True,
            "anomaly_score": 0,
            "risk_level": "LOW",
            "flags": [],
        }), patch("backend.app.pipeline.check_metadata_consistency", return_value={
            "success": True,
            "suspicious": False,
            "flags": [],
        }), patch("backend.app.pipeline.analyze_visual_consistency", return_value={
            "success": True,
            "flags": [],
        }), patch("backend.app.pipeline.calculate_visual_trust_score", return_value={
            "trust_score": 80,
            "flags": [],
        }), patch("backend.app.pipeline.extract_text", return_value={
            "success": False,
            "error": "Image quality too low",
        }), patch("backend.app.pipeline.update_verification_result", side_effect=capture_result), \
                patch("backend.app.pipeline.os.path.exists", return_value=False):
            await _run_pipeline("job-id", "blank.jpg")

        self.assertLessEqual(captured["trust_score"], 50)
        self.assertEqual(
            captured["layers_analyzed"],
            [
                "visual_forensics",
                "content_validation",
                "template_layout_matching",
                "custom_ml_classifier",
            ],
        )
        self.assertIn(
            "OCR failed: Image quality too low",
            captured["flags"],
        )
        self.assertIn(
            "Insufficient text extracted from document",
            captured["flags"],
        )
        self.assertEqual(captured["confidence"], "MEDIUM")

    async def test_successful_ocr_runs_template_layout_matching(self):
        captured = {}

        def capture_result(job_id, result):
            captured.update(result)
            return result

        with patch("backend.app.pipeline.perform_ela", return_value={
            "success": True,
            "anomaly_score": 0,
            "risk_level": "LOW",
            "flags": [],
        }), patch("backend.app.pipeline.check_metadata_consistency", return_value={
            "success": True,
            "suspicious": False,
            "flags": [],
        }), patch("backend.app.pipeline.analyze_visual_consistency", return_value={
            "success": True,
            "flags": [],
        }), patch("backend.app.pipeline.calculate_visual_trust_score", return_value={
            "trust_score": 84,
            "flags": [],
        }), patch("backend.app.pipeline.extract_text", return_value={
            "success": True,
            "text": (
                "THE WEST AFRICAN EXAMINATIONS COUNCIL "
                "Candidate Name ONIBIYO JOLAOLUWA OLUDUNYIN "
                "Examination Number 4251230190 "
                "Examination WASSCE FOR SCHOOL CANDIDATES 2021 "
                "ENGLISH LANGUAGE B2 MATHEMATICS A1"
            ),
            "confidence": 86,
            "word_count": 34,
        }), patch("backend.app.pipeline.validate_certificate_content", return_value={
            "content_score": 88,
            "flags": [],
            "detected_institution": "West African Examinations Council",
        }), patch("backend.app.pipeline.update_verification_result", side_effect=capture_result), \
                patch("backend.app.pipeline.os.path.exists", return_value=False):
            await _run_pipeline("job-id", "waec.jpg")

        self.assertIn("template_layout_matching", captured["layers_analyzed"])
        self.assertIn("custom_ml_classifier", captured["layers_analyzed"])
        self.assertGreaterEqual(captured["trust_score"], 80)
        self.assertEqual(captured["confidence"], "HIGH")
        self.assertTrue(
            any(flag.startswith("AI evidence:") for flag in captured["flags"])
        )
        self.assertTrue(
            any(flag.startswith("ML classifier:") for flag in captured["flags"])
        )

    async def test_trigger_marks_failed_when_pipeline_times_out(self):
        captured = {}

        def capture_failed(verification_id, reason):
            captured["verification_id"] = verification_id
            captured["reason"] = reason

        async def raise_timeout(coro, timeout):
            coro.close()
            raise TimeoutError

        with patch("backend.app.pipeline.asyncio.wait_for", side_effect=raise_timeout), \
                patch("backend.app.pipeline._mark_failed", side_effect=capture_failed):
            await trigger_ai_pipeline("job-id")

        self.assertEqual(captured, {
            "verification_id": "job-id",
            "reason": "Analysis timed out. Please re-submit.",
        })

    async def test_run_pipeline_with_download_marks_failed_when_file_url_missing(self):
        captured = {}
        supabase = _FakeSupabase({"id": "job-id", "file_url": None})

        def capture_failed(verification_id, reason):
            captured["verification_id"] = verification_id
            captured["reason"] = reason

        with patch("backend.app.pipeline.get_supabase", return_value=supabase), \
                patch("backend.app.pipeline._mark_failed", side_effect=capture_failed):
            await _run_pipeline_with_download("job-id")

        self.assertEqual(captured, {
            "verification_id": "job-id",
            "reason": "No file URL found. Upload may have failed.",
        })

    async def test_run_pipeline_with_download_marks_failed_when_read_fails(self):
        captured = {}
        supabase = _FailingSupabase(RuntimeError("database unavailable"))

        def capture_failed(verification_id, reason):
            captured["verification_id"] = verification_id
            captured["reason"] = reason

        with patch("backend.app.pipeline.get_supabase", return_value=supabase), \
                patch("backend.app.pipeline._mark_failed", side_effect=capture_failed):
            await _run_pipeline_with_download("job-id")

        self.assertEqual(captured, {
            "verification_id": "job-id",
            "reason": "Database read error",
        })

    async def test_run_pipeline_with_download_marks_failed_when_record_missing(self):
        captured = {}
        supabase = _FakeSupabase(None)

        def capture_failed(verification_id, reason):
            captured["verification_id"] = verification_id
            captured["reason"] = reason

        with patch("backend.app.pipeline.get_supabase", return_value=supabase), \
                patch("backend.app.pipeline._mark_failed", side_effect=capture_failed):
            await _run_pipeline_with_download("job-id")

        self.assertEqual(captured, {
            "verification_id": "job-id",
            "reason": "Verification record not found",
        })

    async def test_run_pipeline_with_download_marks_failed_when_download_times_out(self):
        captured = {}
        supabase = _FakeSupabase({
            "id": "job-id",
            "status": "PROCESSING",
            "file_url": "https://example.com/cert.jpg",
        })

        def capture_failed(verification_id, reason):
            captured["verification_id"] = verification_id
            captured["reason"] = reason

        with patch("backend.app.pipeline.get_supabase", return_value=supabase), \
                patch(
                    "backend.app.pipeline._download_file",
                    new=AsyncMock(side_effect=httpx.TimeoutException("too slow")),
                ), \
                patch("backend.app.pipeline._mark_failed", side_effect=capture_failed):
            await _run_pipeline_with_download("job-id")

        self.assertEqual(captured, {
            "verification_id": "job-id",
            "reason": "File download timed out",
        })

    async def test_run_pipeline_with_download_marks_failed_when_download_fails(self):
        captured = {}
        supabase = _FakeSupabase({
            "id": "job-id",
            "status": "PROCESSING",
            "file_url": "https://example.com/cert.jpg",
        })

        def capture_failed(verification_id, reason):
            captured["verification_id"] = verification_id
            captured["reason"] = reason

        with patch("backend.app.pipeline.get_supabase", return_value=supabase), \
                patch(
                    "backend.app.pipeline._download_file",
                    new=AsyncMock(side_effect=RuntimeError("bad status")),
                ), \
                patch("backend.app.pipeline._mark_failed", side_effect=capture_failed):
            await _run_pipeline_with_download("job-id")

        self.assertEqual(captured, {
            "verification_id": "job-id",
            "reason": "Could not download certificate file",
        })


class _FakeSupabase:
    def __init__(self, record):
        self.record = record

    def table(self, name):
        return self

    def select(self, columns):
        return self

    def eq(self, column, value):
        return self

    def single(self):
        return self

    def execute(self):
        return SimpleNamespace(data=self.record)


class _FailingSupabase(_FakeSupabase):
    def __init__(self, error):
        self.error = error

    def execute(self):
        raise self.error


if __name__ == "__main__":
    unittest.main()
