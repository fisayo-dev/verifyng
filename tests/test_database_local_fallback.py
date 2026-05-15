import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from postgrest.exceptions import APIError

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

    def test_updates_job_without_supabase_env_using_prd_result_fields(self):
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

        self.assertEqual(updated["status"], "COMPLETE")
        self.assertEqual(stored["trust_score"], 80)
        self.assertEqual(stored["verdict"], "LIKELY AUTHENTIC")
        self.assertEqual(stored["layers_run"], ["visual_forensics"])
        self.assertEqual(stored["confidence"], "HIGH")
        self.assertIn("completed_at", stored)

    def test_update_verification_result_writes_divine_prd_payload_to_supabase(self):
        update_query = Mock()
        update_query.eq.return_value.execute.return_value = SimpleNamespace(
            data=[{"id": "job-id", "status": "COMPLETE"}]
        )
        table = Mock()
        table.update.return_value = update_query

        with patch.dict("os.environ", {
            "SUPABASE_URL": "https://example.supabase.co",
            "SUPABASE_SERVICE_ROLE_KEY": "service-role-key",
        }, clear=True), patch("backend.app.database.get_supabase") as get_supabase:
            get_supabase.return_value.table.return_value = table

            result = database.update_verification_result("job-id", {
                "trust_score": 80,
                "verdict": "LIKELY AUTHENTIC",
                "flags": [],
                "layers_analyzed": ["visual_forensics"],
            })

        self.assertEqual(result, {"id": "job-id", "status": "COMPLETE"})
        table.update.assert_called_once()
        payload = table.update.call_args.args[0]
        self.assertEqual(payload["status"], "COMPLETE")
        self.assertEqual(payload["layers_run"], ["visual_forensics"])
        self.assertEqual(payload["confidence"], "LOW")
        self.assertIn("completed_at", payload)
        self.assertNotIn("layers_analyzed", payload)
        self.assertNotIn("updated_at", payload)
        update_query.eq.assert_called_once_with("id", "job-id")

    def test_create_verification_job_does_not_reuse_supabase_row_by_filename(self):
        existing = {
            "id": "old-job",
            "file_name": "same-name.jpg",
            "status": "pending",
        }
        inserted = {
            "id": "new-job",
            "file_name": "same-name.jpg",
            "temp_file_path": "C:\\tmp\\new.jpg",
            "status": "pending",
        }
        table = Mock()
        table.select.return_value.eq.return_value.execute.return_value = SimpleNamespace(
            data=[existing]
        )
        table.insert.return_value.execute.return_value = SimpleNamespace(
            data=[inserted]
        )

        with patch.dict("os.environ", {
            "SUPABASE_URL": "https://example.supabase.co",
            "SUPABASE_SERVICE_ROLE_KEY": "service-role-key",
        }, clear=True), patch("backend.app.database.get_supabase") as get_supabase:
            get_supabase.return_value.table.return_value = table

            result = database.create_verification_job(
                "same-name.jpg",
                "C:\\tmp\\new.jpg",
            )

        self.assertEqual(result["job_id"], "new-job")
        self.assertFalse(result["cached"])
        table.insert.assert_called_once()

    def test_failed_verdict_maps_to_prd_failed_status(self):
        with patch.dict("os.environ", {}, clear=True):
            job = database.create_verification_job("abc123", "test_cert.jpg")
            updated = database.update_verification_result(job["job_id"], {
                "verdict": "FAILED",
                "flags": ["No file found"],
                "layers_analyzed": [],
            })

        self.assertEqual(updated["status"], "FAILED")

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

    def test_missing_supabase_verification_result_returns_none(self):
        table = Mock()
        table.select.return_value.eq.return_value.single.return_value.execute.side_effect = APIError({
            "code": "PGRST116",
            "details": "The result contains 0 rows",
            "hint": None,
            "message": "Cannot coerce the result to a single JSON object",
        })

        with patch.dict("os.environ", {
            "SUPABASE_URL": "https://example.supabase.co",
            "SUPABASE_SERVICE_ROLE_KEY": "service-role-key",
        }, clear=True), patch("backend.app.database.get_supabase") as get_supabase:
            get_supabase.return_value.table.return_value = table

            result = database.get_verification_result("missing-job")

        self.assertIsNone(result)

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
