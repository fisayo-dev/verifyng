import unittest

from backend.app.ml_model import (
    FEATURE_NAMES,
    classify_certificate,
    get_certificate_classifier,
)


class CertificateMlModelTests(unittest.TestCase):
    def test_custom_classifier_is_trained_from_labeled_cases(self):
        model = get_certificate_classifier()

        self.assertTrue(model["trained"])
        self.assertGreaterEqual(model["training_cases"], 9)
        self.assertEqual(model["feature_names"], FEATURE_NAMES)
        self.assertIn("authentic", model["labels"])
        self.assertIn("forged", model["labels"])

    def test_classifier_predicts_authentic_for_strong_certificate_signals(self):
        result = classify_certificate({
            "visual_score": 86,
            "content_score": 90,
            "template_score": 92,
            "ocr_confidence": 88,
            "ela_anomaly_score": 4,
            "metadata_suspicious": 0,
            "missing_field_count": 0,
            "word_count": 54,
        })

        self.assertEqual(result["ml_prediction"], "authentic")
        self.assertGreaterEqual(result["ml_authenticity_probability"], 0.70)
        self.assertEqual(result["ml_model"], "VerifyNGCustomSoftmaxClassifier")

    def test_classifier_rejects_non_certificate_or_tampered_signals(self):
        result = classify_certificate({
            "visual_score": 42,
            "content_score": 5,
            "template_score": 0,
            "ocr_confidence": 18,
            "ela_anomaly_score": 88,
            "metadata_suspicious": 1,
            "missing_field_count": 5,
            "word_count": 4,
        })

        self.assertEqual(result["ml_prediction"], "forged")
        self.assertLess(result["ml_authenticity_probability"], 0.35)


if __name__ == "__main__":
    unittest.main()
