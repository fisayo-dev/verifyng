import unittest
from types import SimpleNamespace
from unittest.mock import patch

from backend.app.pipeline import (
    _download_file,
    _run_pipeline,
    _run_pipeline_with_download,
    trigger_ai_pipeline,
)


class PipelineEdgeCaseTests(unittest.IsolatedAsyncioTestCase):
    async def test_invalid_verification_id_marks_failed(self):
        supabase = _FakeSupabase(record=None)
        captured = {}

        def capture_failed(verification_id, reason):
            captured["verification_id"] = verification_id
            captured["reason"] = reason

        with patch("backend.app.pipeline.get_supabase", return_value=supabase), \
                patch("backend.app.pipeline._mark_failed", side_effect=capture_failed):
            await trigger_ai_pipeline("non-existent-id")

        self.assertEqual(captured, {
            "verification_id": "non-existent-id",
            "reason": "Verification record not found",
        })

    async def test_missing_file_url_writes_failed(self):
        captured = {}
        supabase = _FakeSupabase(record={"id": "job-id", "file_url": None})

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

    async def test_complete_job_is_idempotent_and_skipped(self):
        supabase = _FakeSupabase(record={
            "id": "job-id",
            "file_url": "https://example.com/cert.jpg",
            "status": "COMPLETE",
        })

        with patch("backend.app.pipeline.get_supabase", return_value=supabase), \
                patch("backend.app.pipeline._download_file") as download_file, \
                patch("backend.app.pipeline._run_pipeline") as run_pipeline:
            await _run_pipeline_with_download("job-id")

        download_file.assert_not_called()
        run_pipeline.assert_not_called()

    async def test_download_failure_writes_failed_not_processing_forever(self):
        captured = {}
        supabase = _FakeSupabase(record={
            "id": "job-id",
            "file_url": "https://example.com/missing.jpg",
            "status": "PROCESSING",
        })

        def capture_failed(verification_id, reason):
            captured["verification_id"] = verification_id
            captured["reason"] = reason

        with patch("backend.app.pipeline.get_supabase", return_value=supabase), \
                patch("backend.app.pipeline._download_file", return_value=None), \
                patch("backend.app.pipeline._mark_failed", side_effect=capture_failed):
            await _run_pipeline_with_download("job-id")

        self.assertEqual(captured, {
            "verification_id": "job-id",
            "reason": "Could not download certificate file",
        })

    async def test_local_file_url_is_supported_for_simulation(self):
        path = "C:\\tmp\\verifyng\\job-id.jpg"

        self.assertEqual(await _download_file(path, "job-id"), path)
        self.assertEqual(await _download_file(f"file:///{path}", "job-id"), path)

    async def test_all_analysis_layers_failing_marks_failed(self):
        captured = {}

        def capture_result(job_id, result):
            captured.update(result)
            return result

        with patch("backend.app.pipeline.perform_ela", side_effect=ValueError("bad image")), \
                patch("backend.app.pipeline.extract_text", side_effect=ValueError("bad image")), \
                patch("backend.app.pipeline.classify_certificate", side_effect=ValueError("no features")), \
                patch("backend.app.pipeline.update_verification_result", side_effect=capture_result), \
                patch("backend.app.pipeline.os.path.exists", return_value=False):
            await _run_pipeline("job-id", "corrupt.jpg")

        self.assertEqual(captured["verdict"], "FAILED")
        self.assertEqual(captured["status"], "FAILED")
        self.assertEqual(captured["confidence"], "LOW")
        self.assertTrue(captured["flags"])


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


if __name__ == "__main__":
    unittest.main()
