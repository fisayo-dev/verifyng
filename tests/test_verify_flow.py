import unittest
import uuid
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


class VerifyFlowTests(unittest.TestCase):
    def test_verify_is_divine_owned_stub(self):
        response = client.post("/verify")

        self.assertEqual(response.status_code, 501)
        self.assertEqual(response.json(), {
            "detail": "Divine owns the full /verify implementation. Call /trigger/{job_id} after payment and upload are complete."
        })

    def test_old_ai_test_endpoints_are_removed(self):
        self.assertEqual(client.get("/").status_code, 404)
        self.assertEqual(client.get("/test-ocr").status_code, 404)
        self.assertEqual(client.get("/test-ela").status_code, 404)

    def test_trigger_queues_pipeline_demo_task(self):
        job_id = str(uuid.uuid4())

        with patch("backend.app.main.trigger_ai_pipeline") as trigger_pipeline:
            response = client.post(f"/trigger/{job_id}")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            "job_id": job_id,
            "status": "PROCESSING",
            "message": "AI pipeline queued for demo trigger.",
        })
        trigger_pipeline.assert_called_once_with(job_id)

    def test_result_returns_stored_verification_job(self):
        job_id = str(uuid.uuid4())
        stored_result = {
            "id": job_id,
            "status": "COMPLETE",
            "file_hash": "abc123",
            "trust_score": 82,
            "verdict": "LIKELY AUTHENTIC",
            "flags": [],
            "layers_run": ["visual_forensics", "content_validation"],
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
            "status": "COMPLETE",
            "trust_score": 82,
            "verdict": "LIKELY AUTHENTIC",
            "flags": [],
            "confidence": "HIGH",
            "layers_run": ["visual_forensics", "content_validation"],
        }
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected_result)
        self.assertEqual(set(response.json()), set(expected_result))

    def test_result_returns_pending_payment_contract(self):
        job_id = str(uuid.uuid4())

        with patch("backend.app.main.get_verification_result", return_value={
            "id": job_id,
            "status": "PENDING_PAYMENT",
            "trust_score": None,
            "verdict": None,
            "flags": [],
            "confidence": None,
            "layers_run": [],
        }):
            response = client.get(f"/result/{job_id}")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "PENDING_PAYMENT"})

    def test_result_returns_processing_contract(self):
        job_id = str(uuid.uuid4())

        with patch("backend.app.main.get_verification_result", return_value={
            "id": job_id,
            "status": "PROCESSING",
            "trust_score": None,
            "verdict": None,
            "flags": [],
            "confidence": None,
            "layers_run": [],
        }):
            response = client.get(f"/result/{job_id}")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "PROCESSING"})

    def test_result_returns_failed_contract(self):
        job_id = str(uuid.uuid4())

        with patch("backend.app.main.get_verification_result", return_value={
            "id": job_id,
            "status": "FAILED",
            "trust_score": None,
            "verdict": "FAILED",
            "flags": ["Could not download certificate file"],
            "confidence": "LOW",
            "layers_run": [],
        }):
            response = client.get(f"/result/{job_id}")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            "status": "FAILED",
            "flags": ["Could not download certificate file"],
        })

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
