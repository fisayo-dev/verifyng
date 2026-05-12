import io
import unittest
import uuid
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


async def noop_pipeline(job_id: str, file_path: str):
    return None


class VerifyFlowTests(unittest.TestCase):
    def test_verify_returns_processing_job_response(self):
        job_id = "550e8400-e29b-41d4-a716-446655440000"

        with patch("backend.app.main.create_verification_job") as create_job, \
                patch("backend.app.main.create_payment_record") as create_payment, \
                patch("backend.app.main.run_ai_pipeline", noop_pipeline):
            create_job.return_value = {
                "job_id": job_id,
                "cached": False,
                "data": {"id": job_id, "status": "pending"},
            }
            create_payment.return_value = {
                "squad_ref": "VNG-550e8400",
                "status": "pending",
            }

            response = client.post(
                "/verify",
                files={"file": ("test_cert.jpg", io.BytesIO(b"fake image bytes"), "image/jpeg")},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            "job_id": job_id,
            "squad_ref": "VNG-550e8400",
            "payment_amount": 500,
            "currency": "NGN",
            "cached": False,
            "status": "processing",
            "message": "Certificate received. Processing started.",
            "poll_url": f"/result/{job_id}",
        })
        create_job.assert_called_once()
        create_payment.assert_called_once_with("VNG-550e8400", job_id)

    def test_verify_returns_cached_true_for_existing_file(self):
        job_id = "550e8400-e29b-41d4-a716-446655440000"

        with patch("backend.app.main.create_verification_job") as create_job, \
                patch("backend.app.main.create_payment_record"), \
                patch("backend.app.main.run_ai_pipeline", noop_pipeline):
            create_job.return_value = {
                "job_id": job_id,
                "cached": True,
                "data": {"id": job_id, "status": "completed"},
            }

            response = client.post(
                "/verify",
                files={"file": ("test_cert.jpg", io.BytesIO(b"same image bytes"), "image/jpeg")},
            )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["cached"])
        self.assertEqual(response.json()["job_id"], job_id)

    def test_result_returns_stored_verification_job(self):
        job_id = str(uuid.uuid4())
        stored_result = {
            "id": job_id,
            "status": "completed",
            "file_hash": "abc123",
            "trust_score": 82,
            "verdict": "LIKELY AUTHENTIC",
            "flags": [],
            "layers_analyzed": ["visual_forensics", "content_validation"],
            "confidence": "HIGH",
            "file_name": "test_cert.jpg",
            "created_at": "2026-05-12T10:34:41.062123+00:00",
            "updated_at": "2026-05-12T17:46:59.175276+00:00",
            "payments": [{"squad_ref": f"VNG-{job_id[:8]}", "status": "pending"}],
        }

        with patch("backend.app.main.get_verification_result", return_value=stored_result):
            response = client.get(f"/result/{job_id}")

        expected_result = {
            "id": job_id,
            "file_hash": "abc123",
            "trust_score": 82,
            "verdict": "LIKELY AUTHENTIC",
            "flags": [],
            "layers_analyzed": ["visual_forensics", "content_validation"],
            "confidence": "HIGH",
            "status": "completed",
        }
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected_result)

    def test_result_returns_404_when_job_is_missing(self):
        job_id = str(uuid.uuid4())

        with patch("backend.app.main.get_verification_result", return_value=None):
            response = client.get(f"/result/{job_id}")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"detail": "Verification job not found"})

    def test_result_returns_404_for_invalid_job_id(self):
        with patch("backend.app.main.get_verification_result") as get_result:
            response = client.get("/result/fake-id-that-does-not-exist")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"detail": "Verification job not found"})
        get_result.assert_not_called()

    def test_result_returns_503_when_database_is_unreachable(self):
        job_id = str(uuid.uuid4())

        with patch(
            "backend.app.main.get_verification_result",
            side_effect=ConnectionError("database hostname could not be resolved"),
        ):
            response = client.get(f"/result/{job_id}")

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json(), {
            "detail": "Verification database is temporarily unavailable"
        })


if __name__ == "__main__":
    unittest.main()
