import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

from backend.app import payments


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
        create_payment_record.assert_not_called()

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


if __name__ == "__main__":
    unittest.main()
