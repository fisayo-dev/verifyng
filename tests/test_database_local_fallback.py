import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from backend.app import database


class LocalDatabaseFallbackTests(unittest.TestCase):
    def setUp(self):
        database.reset_local_store()

    def tearDown(self):
        database.reset_local_store()

    def test_creates_and_fetches_job_without_supabase_env(self):
        with patch.dict("os.environ", {}, clear=True):
            job = database.create_verification_job("abc123", "test_cert.jpg")
            payment = database.create_payment_record("VNG-12345678", job["job_id"])
            stored = database.get_verification_result(job["job_id"])

        self.assertFalse(job["cached"])
        self.assertEqual(job["data"]["status"], "pending")
        self.assertEqual(payment["status"], "pending")
        self.assertEqual(stored["id"], job["job_id"])
        self.assertEqual(stored["payments"][0]["squad_ref"], "VNG-12345678")

    def test_updates_job_without_supabase_env(self):
        with patch.dict("os.environ", {}, clear=True):
            job = database.create_verification_job("abc123", "test_cert.jpg")
            updated = database.update_verification_result(job["job_id"], {
                "trust_score": 80,
                "verdict": "LIKELY AUTHENTIC",
                "flags": [],
                "layers_analyzed": ["visual_forensics"],
                "confidence": "HIGH",
            })
            stored = database.get_verification_result(job["job_id"])

        self.assertEqual(updated["status"], "completed")
        self.assertEqual(stored["trust_score"], 80)
        self.assertEqual(stored["verdict"], "LIKELY AUTHENTIC")

    def test_create_payment_record_is_idempotent_without_supabase_env(self):
        with patch.dict("os.environ", {}, clear=True):
            job = database.create_verification_job("abc123", "test_cert.jpg")
            first = database.create_payment_record("VNG-12345678", job["job_id"])
            second = database.create_payment_record("VNG-12345678", job["job_id"])

        self.assertEqual(first, second)
        self.assertEqual(first["squad_ref"], "VNG-12345678")

    def test_create_payment_record_reuses_existing_supabase_payment(self):
        existing = {
            "squad_ref": "VNG-12345678",
            "verification_id": "job-id",
            "status": "pending",
        }
        table = Mock()
        table.select.return_value.eq.return_value.execute.return_value = SimpleNamespace(
            data=[existing]
        )

        with patch.dict("os.environ", {
            "SUPABASE_URL": "https://example.supabase.co",
            "SUPABASE_SERVICE_ROLE_KEY": "service-role-key",
        }, clear=True), patch("backend.app.database.get_supabase") as get_supabase:
            get_supabase.return_value.table.return_value = table

            result = database.create_payment_record("VNG-12345678", "job-id")

        self.assertEqual(result, existing)
        table.insert.assert_not_called()

    def test_backend_env_path_is_known(self):
        self.assertTrue(database.BACKEND_ENV_PATH.endswith("backend\\.env"))

    def test_service_role_key_is_preferred_for_backend_client(self):
        with patch.dict("os.environ", {
            "SUPABASE_URL": "https://example.supabase.co",
            "SUPABASE_KEY": "anon-key",
            "SUPABASE_SERVICE_ROLE_KEY": "service-role-key",
        }, clear=True):
            self.assertEqual(database.get_supabase_key(), "service-role-key")

    def test_public_supabase_key_is_used_when_service_role_key_is_absent(self):
        with patch.dict("os.environ", {
            "SUPABASE_URL": "https://example.supabase.co",
            "SUPABASE_KEY": "anon-key",
        }, clear=True):
            self.assertEqual(database.get_supabase_key(), "anon-key")


if __name__ == "__main__":
    unittest.main()
