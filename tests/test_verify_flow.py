import unittest
import uuid
from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient
from postgrest.exceptions import APIError

from backend.app.main import app


client = TestClient(app)


class VerifyFlowTests(unittest.TestCase):
    def test_main_only_exposes_owned_routes(self):
        self.assertEqual(client.get("/health").status_code, 200)
        self.assertEqual(client.post("/verify").status_code, 404)
        self.assertEqual(client.post("/api/verify").status_code, 422)
        self.assertEqual(client.post("/api/webhook/squad").status_code, 404)
        self.assertEqual(client.post(f"/trigger/{uuid.uuid4()}").status_code, 404)

    def test_verify_upload_returns_job_and_api_poll_url_without_squad_key(self):
        from backend.app.database import reset_local_store

        reset_local_store()
        nonraising_client = TestClient(app, raise_server_exceptions=False)

        with patch.dict("os.environ", {}, clear=True):
            response = nonraising_client.post(
                "/api/verify",
                files={"file": ("sample.jpg", b"sample bytes", "image/jpeg")},
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["job_id"])
        self.assertEqual(payload["checkout_url"], "")
        self.assertEqual(payload["status"], "PENDING_PAYMENT")
        self.assertEqual(
            payload["poll_url"],
            f"https://olatunjitobi-verifyng-api.hf.space/api/result/{payload['job_id']}",
        )

    def test_verify_upload_initiates_squad_payment_in_kobo(self):
        from backend.app.database import reset_local_store

        reset_local_store()
        captured = {}

        async def fake_initiate_payment(amount, email, verification_id):
            captured.update({
                "amount": amount,
                "email": email,
                "verification_id": verification_id,
            })
            return {
                "data": {
                    "checkout_url": "https://checkout.squadco.com/test",
                }
            }

        with patch.dict("os.environ", {"SQUAD_API_KEY": "sandbox-key"}, clear=True), \
                patch("backend.app.payments.initiate_payment", side_effect=fake_initiate_payment):
            response = client.post(
                "/api/verify",
                files={"file": ("sample.jpg", b"sample bytes", "image/jpeg")},
            )

        payload = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(captured["amount"], 50000)
        self.assertEqual(payload["checkout_url"], "https://checkout.squadco.com/test")

    def test_result_returns_processing_without_private_scores(self):
        job_id = str(uuid.uuid4())
        supabase = _FakeSupabase(select_data={
            "id": job_id,
            "status": "PROCESSING",
            "trust_score": 82,
            "verdict": "LIKELY AUTHENTIC",
        })

        with patch("backend.app.result.get_supabase", return_value=supabase):
            response = client.get(f"/api/result/{job_id}")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            "verification_id": job_id,
            "status": "PROCESSING",
            "message": "AI is analyzing your certificate...",
        })

    def test_result_returns_failed_with_refund_eligible(self):
        job_id = str(uuid.uuid4())
        supabase = _FakeSupabase(select_data={
            "id": job_id,
            "status": "FAILED",
            "trust_score": None,
            "verdict": "FAILED",
        })

        with patch("backend.app.result.get_supabase", return_value=supabase):
            response = client.get(f"/api/result/{job_id}")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            "verification_id": job_id,
            "status": "FAILED",
            "message": "Verification failed. Please contact support.",
            "refund_eligible": True,
        })

    def test_result_returns_complete_contract(self):
        job_id = str(uuid.uuid4())
        supabase = _FakeSupabase(select_data={
            "id": job_id,
            "status": "COMPLETE",
            "trust_score": 82,
            "verdict": "LIKELY AUTHENTIC",
            "flags": ["AI evidence: visual=80"],
            "confidence": "HIGH",
            "layers_run": ["visual_forensics", "content_validation"],
            "report_url": "https://example.com/report.pdf",
        })

        with patch("backend.app.result.get_supabase", return_value=supabase):
            response = client.get(f"/api/result/{job_id}")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            "verification_id": job_id,
            "status": "COMPLETE",
            "trust_score": 82,
            "verdict": "LIKELY AUTHENTIC",
            "flags": ["AI evidence: visual=80"],
            "confidence": "HIGH",
            "layers_run": ["visual_forensics", "content_validation"],
            "report_url": "https://example.com/report.pdf",
        })

    def test_result_returns_404_when_job_is_missing(self):
        job_id = str(uuid.uuid4())
        supabase = _FakeSupabase(select_data=None)

        with patch("backend.app.result.get_supabase", return_value=supabase):
            response = client.get(f"/api/result/{job_id}")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {
            "detail": {
                "error": "NOT_FOUND",
                "message": "Verification ID not found",
            }
        })

    def test_result_returns_404_when_supabase_single_row_is_missing(self):
        job_id = str(uuid.uuid4())
        supabase = _ErroringSupabase(APIError({
            "code": "PGRST116",
            "details": "The result contains 0 rows",
            "hint": None,
            "message": "Cannot coerce the result to a single JSON object",
        }))

        with patch("backend.app.result.get_supabase", return_value=supabase):
            response = client.get(f"/api/result/{job_id}")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {
            "detail": {
                "error": "NOT_FOUND",
                "message": "Verification ID not found",
            }
        })

    def test_result_returns_404_for_invalid_uuid(self):
        response = client.get("/api/result/fake-id-123")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {
            "detail": {
                "error": "NOT_FOUND",
                "message": "Verification ID not found",
            }
        })

    def test_report_returns_url_only_after_completion(self):
        job_id = str(uuid.uuid4())
        supabase = _FakeSupabase(select_data={
            "id": job_id,
            "status": "COMPLETE",
            "report_url": "https://example.com/report.pdf",
        })

        with patch("backend.app.result.get_supabase", return_value=supabase):
            response = client.get(f"/api/report/{job_id}")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            "verification_id": job_id,
            "report_url": "https://example.com/report.pdf",
        })

    def test_report_returns_409_when_not_ready(self):
        job_id = str(uuid.uuid4())
        supabase = _FakeSupabase(select_data={
            "id": job_id,
            "status": "PROCESSING",
            "report_url": None,
        })

        with patch("backend.app.result.get_supabase", return_value=supabase):
            response = client.get(f"/api/report/{job_id}")

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json(), {
            "detail": {
                "error": "REPORT_NOT_READY",
                "message": "Report is not available until verification is complete.",
            }
        })

    def test_manual_trigger_requires_configured_api_key(self):
        job_id = str(uuid.uuid4())

        with patch.dict("os.environ", {}, clear=True):
            response = client.post(f"/api/trigger/{job_id}")

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json(), {"detail": "Invalid API key"})

    def test_manual_trigger_rejects_missing_file_url(self):
        job_id = str(uuid.uuid4())
        supabase = _FakeSupabase(select_data={
            "id": job_id,
            "status": "PAID",
            "file_url": None,
        })

        with patch.dict("os.environ", {"API_KEY": "secret"}, clear=True), \
                patch("backend.app.result.get_supabase", return_value=supabase):
            response = client.post(
                f"/api/trigger/{job_id}",
                headers={"X-API-Key": "secret"},
            )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(),
            {"detail": "file_url is not set. Divine must upload the file first."},
        )

    def test_manual_trigger_sets_processing_and_queues_pipeline(self):
        job_id = str(uuid.uuid4())
        queued = []
        supabase = _FakeSupabase(select_data={
            "id": job_id,
            "status": "PAID",
            "file_url": "https://example.com/certificate.jpg",
        })

        async def capture_trigger(verification_id):
            queued.append(verification_id)

        with patch.dict("os.environ", {"API_KEY": "secret"}, clear=True), \
                patch("backend.app.result.get_supabase", return_value=supabase), \
                patch("backend.app.result.trigger_ai_pipeline", side_effect=capture_trigger):
            response = client.post(
                f"/api/trigger/{job_id}",
                headers={"X-API-Key": "secret"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            "status": "triggered",
            "verification_id": job_id,
            "poll_url": f"/api/result/{job_id}",
        })
        self.assertEqual(supabase.updated, {"status": "PROCESSING"})
        self.assertEqual(queued, [job_id])


class _FakeSupabase:
    def __init__(self, select_data):
        self.select_data = select_data
        self.updated = None

    def table(self, name):
        return self

    def select(self, columns):
        return self

    def update(self, payload):
        self.updated = payload
        return self

    def eq(self, column, value):
        return self

    def single(self):
        return self

    def execute(self):
        return SimpleNamespace(data=self.select_data)


class _ErroringSupabase:
    def __init__(self, error):
        self.error = error

    def table(self, name):
        return self

    def select(self, columns):
        return self

    def eq(self, column, value):
        return self

    def single(self):
        return self

    def execute(self):
        raise self.error


if __name__ == "__main__":
    unittest.main()
