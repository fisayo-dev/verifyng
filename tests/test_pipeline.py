import unittest
from unittest.mock import patch

from backend.app.main import run_ai_pipeline


class PipelineTests(unittest.IsolatedAsyncioTestCase):
    async def test_ocr_failure_contributes_low_content_score(self):
        captured = {}

        def capture_result(job_id, result):
            captured.update(result)
            return result

        with patch("backend.app.main.perform_ela", return_value={
            "success": True,
            "anomaly_score": 0,
            "risk_level": "LOW",
            "flags": [],
        }), patch("backend.app.main.check_metadata_consistency", return_value={
            "success": True,
            "suspicious": False,
            "flags": [],
        }), patch("backend.app.main.analyze_visual_consistency", return_value={
            "success": True,
            "flags": [],
        }), patch("backend.app.main.extract_text", return_value={
            "success": False,
            "error": "Image quality too low",
        }), patch("backend.app.main.update_verification_result", side_effect=capture_result), \
                patch("backend.app.main.os.path.exists", return_value=False):
            await run_ai_pipeline("job-id", "blank.jpg")

        self.assertLessEqual(captured["trust_score"], 50)
        self.assertIn("content_validation", captured["layers_analyzed"])
        self.assertIn(
            "Insufficient text extracted from document",
            captured["flags"],
        )


if __name__ == "__main__":
    unittest.main()
