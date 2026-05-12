import tempfile
import unittest
from pathlib import Path

from PIL import Image

from backend.app.ela import calculate_visual_trust_score, check_metadata_consistency


class ElaTests(unittest.TestCase):
    def test_missing_exif_uses_pdf_conversion_friendly_message(self):
        expected_message = (
            "Image metadata unavailable, common for PDF conversions or scanned documents"
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            image_path = Path(tmpdir) / "certificate.jpg"
            Image.new("RGB", (20, 20), "white").save(image_path)

            result = check_metadata_consistency(str(image_path))

        self.assertEqual(result["flags"], [expected_message])

    def test_high_ela_anomaly_produces_low_visual_trust(self):
        ela_result = {
            "success": True,
            "anomaly_score": 79.19,
            "risk_level": "HIGH",
            "flags": ["Extreme pixel differences found in specific regions"],
        }
        metadata_result = {
            "success": True,
            "suspicious": False,
            "flags": [],
        }
        visual_result = {
            "success": True,
            "flags": [],
        }

        result = calculate_visual_trust_score(
            ela_result, metadata_result, visual_result
        )

        self.assertLessEqual(result["trust_score"], 20)
        self.assertEqual(
            result["flags"],
            ["Extreme pixel differences found in specific regions"],
        )


if __name__ == "__main__":
    unittest.main()
