import unittest

from backend.app.ai_depth import (
    benchmark_verification_cases,
    build_ai_evidence_report,
    score_template_match,
)
from backend.app.ocr import extract_text


WAEC_TEXT = """
THE WEST AFRICAN
EXAMINATIONS COUNCIL
Candidate Information
Examination Number 4251230190
Candidate Name ONIBIYO JOLAOLUWA OLUDUNYIN
Examination WASSCE FOR SCHOOL CANDIDATES 2021
Subject Grades
ENGLISH LANGUAGE B2
MATHEMATICS A1
"""


class AiDepthTests(unittest.TestCase):
    def test_waec_template_match_scores_required_fields_and_layout(self):
        result = score_template_match(WAEC_TEXT, ocr_confidence=86)

        self.assertEqual(result["detected_template"], "WAEC WASSCE Result")
        self.assertGreaterEqual(result["template_score"], 90)
        self.assertEqual(result["field_scores"]["institution"], 100)
        self.assertEqual(result["field_scores"]["candidate_name"], 100)
        self.assertEqual(result["field_scores"]["examination_number"], 100)
        self.assertEqual(result["field_scores"]["grade_table"], 100)
        self.assertEqual(result["flags"], [])

    def test_non_certificate_text_is_rejected_by_template_matcher(self):
        result = score_template_match(
            "hello this is a random image receipt with no certificate fields",
            ocr_confidence=40,
        )

        self.assertLessEqual(result["template_score"], 35)
        self.assertIsNone(result["detected_template"])
        self.assertIn("Document does not match WAEC certificate template", result["flags"])
        self.assertIn("OCR confidence below review threshold", result["flags"])

    def test_real_waec_screenshot_layout_scores_as_template_match(self):
        text = """
        THE WEST AFRICAN EXAMINATIONS COUNCIL
        WAECDIRECT ONLINE - RESULTS
        Examination Number Candidate's Name Examination Centre
        CHRISTIAN RELIGIOUS STUDIES CIVIC EDUCATION ENGLISH LANGUAGE MATHEMATICS
        BIOLOGY CHEMISTRY PHYSICS COMPUTER STUDIES CATERING CRAFT PRACTICE
        4020614054 NZEKWE EBUBECHUKWU REJOICE
        WASSCE FOR SCHOOL CANDIDATES 2023
        REGINA PACIS GIRLS SECONDARY SCHOOL GARKI
        """

        result = score_template_match(text, ocr_confidence=87.17)

        self.assertEqual(result["detected_template"], "WAEC WASSCE Result")
        self.assertGreaterEqual(result["template_score"], 85)
        self.assertGreaterEqual(result["field_scores"]["candidate_name"], 80)
        self.assertGreaterEqual(result["field_scores"]["grade_table"], 80)

    def test_ocr_noisy_waec_screenshot_still_gets_partial_template_match(self):
        text = """
        THE WEST AFRICA EKRMINATIONS COUNCIL
        Candidate's Information
        Examination Number Candidate's Name Examination Centre Subject/Grade
        DATA PROCESSING CIVIC EDUCATION ENGLISH LANGUAGE FURTHER MATHEMATICS
        BIOLOGY CHEMISTRY PHYSICS
        4281570143 MASON DAVID OLUDAMINOLA
        WASSCE FOR SCHOOL CANDIDATES 2023
        """

        result = score_template_match(text, ocr_confidence=86.55)

        self.assertGreaterEqual(result["template_score"], 70)
        self.assertEqual(result["detected_template"], "WAEC WASSCE Result")

    def test_ai_evidence_report_exposes_interpretable_signals(self):
        report = build_ai_evidence_report(
            visual_score=82,
            content_score=88,
            template_result=score_template_match(WAEC_TEXT, ocr_confidence=86),
            ocr_result={"confidence": 86, "word_count": 34},
        )

        self.assertEqual(report["technical_depth_score"], 30)
        self.assertEqual(report["signal_scores"]["visual_forensics"], 82)
        self.assertEqual(report["signal_scores"]["content_validation"], 88)
        self.assertGreaterEqual(report["signal_scores"]["template_match"], 90)
        self.assertEqual(report["signal_scores"]["ocr_confidence"], 86)
        self.assertIn("visual forensics", report["judge_summary"].lower())
        self.assertIn("template", report["judge_summary"].lower())

    def test_benchmark_verification_cases_reports_accuracy_and_confusion_matrix(self):
        cases = [
            {"name": "clean", "expected": "authentic", "trust_score": 88},
            {"name": "manual", "expected": "review", "trust_score": 62},
            {"name": "fake", "expected": "forged", "trust_score": 18},
            {"name": "tampered", "expected": "forged", "trust_score": 44},
        ]

        report = benchmark_verification_cases(cases)

        self.assertEqual(report["total_cases"], 4)
        self.assertEqual(report["accuracy"], 100.0)
        self.assertEqual(report["confusion_matrix"]["authentic"]["authentic"], 1)
        self.assertEqual(report["confusion_matrix"]["review"]["review"], 1)
        self.assertEqual(report["confusion_matrix"]["forged"]["forged"], 2)

    def test_real_sideways_waec_image_is_auto_oriented_for_ocr(self):
        ocr = extract_text("backend/real_waec_certificates/david's waec.JPG")
        template = score_template_match(ocr.get("text", ""), ocr.get("confidence") or 0)

        self.assertTrue(ocr["success"])
        self.assertGreaterEqual(ocr["confidence"], 80)
        self.assertGreaterEqual(template["template_score"], 70)


if __name__ == "__main__":
    unittest.main()
