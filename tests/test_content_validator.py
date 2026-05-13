import unittest
from unittest.mock import patch

from backend.app import content_validator
from backend.app.content_validator import validate_certificate_content


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
https://www.waecdirect.org/DisplayResult.aspx?ExamYear=2021
"""


class ContentValidatorTests(unittest.TestCase):
    def test_waec_result_detects_institution_candidate_and_full_year(self):
        content_validator._cached_formats = None
        with patch("backend.app.content_validator.get_institution_formats", return_value=[]):
            result = validate_certificate_content(WAEC_TEXT)

        self.assertEqual(
            result["detected_institution"],
            "West African Examinations Council",
        )
        self.assertEqual(result["detected_cert_type"], "WASSCE Result")
        self.assertIn("2021", result["years_found"])
        self.assertNotIn("20", result["years_found"])
        self.assertNotIn(
            "No recognized Nigerian institution found in document",
            result["flags"],
        )
        self.assertNotIn(
            "Could not detect candidate name pattern",
            result["flags"],
        )
        self.assertFalse(
            any(flag.startswith("Suspicious year detected") for flag in result["flags"])
        )

    def test_partial_year_is_ignored(self):
        text = """
        THE WEST AFRICAN EXAMINATIONS COUNCIL
        Candidate Name ADA LOVELACE TESTER
        Examination Number 1234567890
        WASSCE FOR SCHOOL CANDIDATES
        Page 1 of 20
        """

        content_validator._cached_formats = None
        with patch("backend.app.content_validator.get_institution_formats", return_value=[]):
            result = validate_certificate_content(text)

        self.assertNotIn("20", result["years_found"])
        self.assertNotIn("Suspicious year detected: 20", result["flags"])

    def test_waec_builtin_format_takes_priority_over_generic_database_match(self):
        content_validator._cached_formats = None
        generic_format = {
            "name": "Generic WAEC",
            "cert_type": "SSCE",
            "known_keywords": ["WEST AFRICAN", "EXAMINATIONS COUNCIL"],
        }

        with patch(
            "backend.app.content_validator.get_institution_formats",
            return_value=[generic_format],
        ):
            result = validate_certificate_content(WAEC_TEXT)

        self.assertEqual(result["detected_cert_type"], "WASSCE Result")
        self.assertEqual(result["years_found"], ["2021"])


if __name__ == "__main__":
    unittest.main()
