import unittest
from unittest.mock import patch

from backend.app.pipeline import _run_pipeline


class PipelineTests(unittest.IsolatedAsyncioTestCase):
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

        self.assertEqual(captured["trust_score"], 80)
        self.assertEqual(captured["layers_analyzed"], ["visual_forensics"])
        self.assertIn(
            "OCR failed: Image quality too low",
            captured["flags"],
        )


if __name__ == "__main__":
    unittest.main()
