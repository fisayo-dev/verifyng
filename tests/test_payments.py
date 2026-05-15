import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

from fastapi.testclient import TestClient

from backend.app import payments
from backend.app.main import app


client = TestClient(app)


class PaymentsTests(unittest.IsolatedAsyncioTestCase):
    async def test_initiate_payment_uses_nested_squad_transaction_ref(self):
        payload = {
            "success": True,
            "data": {
                "transaction_ref": "SQD_REF_123",
                "checkout_url": "https://checkout.squadco.com/pay",
            },
        }
        response = Mock()
        response.json.return_value = payload
        response.raise_for_status.return_value = None

        client = AsyncMock()
        client.post.return_value = response
        client.__aenter__.return_value = client
        client.__aexit__.return_value = None

        with patch.dict("os.environ", {"SQUAD_API_KEY": "sandbox-key"}, clear=True), \
                patch("backend.app.payments.SQUAD_API_KEY", "sandbox-key"), \
                patch("backend.app.payments.httpx.AsyncClient", return_value=client), \
                patch("backend.app.payments.create_payment_record") as create_payment_record:
            result = await payments.initiate_payment(
                amount=50000,
                email="customer@example.com",
                verification_id="verification-id",
            )

        self.assertEqual(result, payload)
        create_payment_record.assert_called_once_with(
            squad_ref="SQD_REF_123",
            verification_id="verification-id",
        )

    async def test_initiate_payment_accepts_common_checkout_url_shapes(self):
        payload = {
            "success": True,
            "data": {
                "checkout_url": "https://checkout.squadco.com/pay",
            },
        }
        response = Mock()
        response.json.return_value = payload
        response.raise_for_status.return_value = None

        client = AsyncMock()
        client.post.return_value = response
        client.__aenter__.return_value = client
        client.__aexit__.return_value = None

        with patch.dict("os.environ", {"SQUAD_API_KEY": "sandbox-key"}, clear=True), \
                patch("backend.app.payments.SQUAD_API_KEY", "sandbox-key"), \
                patch("backend.app.payments.httpx.AsyncClient", return_value=client), \
                patch("backend.app.payments.create_payment_record") as create_payment_record:
            result = await payments.initiate_payment(
                amount=50000,
                email="customer@example.com",
                verification_id="verification-id",
            )

        self.assertEqual(result, payload)
        create_payment_record.assert_called_once_with(
            squad_ref="VNG-verification-id",
            verification_id="verification-id",
        )

    async def test_initiate_payment_normalizes_nested_authorization_url(self):
        payload = {
            "success": True,
            "data": {
                "transaction_ref": "SQD_REF_123",
                "authorization_url": "https://checkout.squadco.com/pay",
            },
        }
        response = Mock()
        response.json.return_value = payload
        response.raise_for_status.return_value = None

        client = AsyncMock()
        client.post.return_value = response
        client.__aenter__.return_value = client
        client.__aexit__.return_value = None

        with patch.dict("os.environ", {"SQUAD_API_KEY": "sandbox-key"}, clear=True), \
                patch("backend.app.payments.SQUAD_API_KEY", "sandbox-key"), \
                patch("backend.app.payments.httpx.AsyncClient", return_value=client), \
                patch("backend.app.payments.create_payment_record"):
            result = await payments.initiate_payment(
                amount=50000,
                email="customer@example.com",
                verification_id="verification-id",
            )

        self.assertEqual(
            result["data"]["checkout_url"],
            "https://checkout.squadco.com/pay",
        )

    async def test_initiate_payment_sends_reference_and_backend_callback_url(self):
        payload = {
            "success": True,
            "data": {
                "transaction_ref": "VNG-verification-id",
                "checkout_url": "https://checkout.squadco.com/pay",
            },
        }
        response = Mock()
        response.json.return_value = payload
        response.raise_for_status.return_value = None

        http_client = AsyncMock()
        http_client.post.return_value = response
        http_client.__aenter__.return_value = http_client
        http_client.__aexit__.return_value = None

        with patch.dict("os.environ", {"SQUAD_API_KEY": "sandbox-key"}, clear=True), \
                patch("backend.app.payments.SQUAD_API_KEY", "sandbox-key"), \
                patch(
                    "backend.app.payments.WEBHOOK_URL",
                    "https://api.example.com/api/payment/callback",
                ), \
                patch("backend.app.payments.httpx.AsyncClient", return_value=http_client), \
                patch("backend.app.payments.create_payment_record"):
            await payments.initiate_payment(
                amount=50000,
                email="customer@example.com",
                verification_id="verification-id",
            )

        request_payload = http_client.post.call_args.kwargs["json"]
        self.assertEqual(request_payload["transaction_ref"], "VNG-verification-id")
        self.assertEqual(
            request_payload["callback_url"],
            "https://api.example.com/api/payment/callback",
        )
        self.assertEqual(http_client.post.call_args.kwargs["timeout"], 10.0)

    def test_payment_callback_marks_paid_queues_pipeline_and_redirects_to_result(self):
        verification_id = "550e8400-e29b-41d4-a716-446655440000"
        verify_payment = AsyncMock()

        with patch.dict("os.environ", {
            "FRONTEND_URL": "https://verifyng-three.vercel.app",
        }, clear=True), \
                patch("backend.app.payments.confirm_payment", return_value={
                    "squad_ref": f"VNG-{verification_id}",
                    "verification_id": verification_id,
                }), \
                patch("backend.app.payments.get_verification_result", return_value={
                    "id": verification_id,
                    "temp_file_path": "C:\\tmp\\cert.jpg",
                    "file_url": None,
                }), \
                patch("backend.app.payments.verify_payment", verify_payment):
            response = client.get(
                f"/api/payment/callback?transaction_ref=VNG-{verification_id}",
                follow_redirects=False,
            )

        self.assertEqual(response.status_code, 307)
        self.assertEqual(
            response.headers["location"],
            f"https://verifyng-three.vercel.app/results/{verification_id}",
        )
        verify_payment.assert_called_once_with(
            verification_id,
            "C:\\tmp\\cert.jpg",
            f"VNG-{verification_id}",
        )


if __name__ == "__main__":
    unittest.main()
