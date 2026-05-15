import logging
import os

import httpx
from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from fastapi.responses import RedirectResponse

from .database import get_payment_by_squad_ref, get_verification_result, confirm_payment, create_payment_record
from .verifications import verify_payment
from .pipeline import trigger_ai_pipeline

logger = logging.getLogger(__name__)

SQUAD_API_URL = os.getenv("SQUAD_API_URL", "https://sandbox-api-d.squadco.com")
SQUAD_API_KEY = os.getenv("SQUAD_API_KEY")
WEBHOOK_URL = os.getenv(
    "WEBHOOK_URL",
    "https://olatunjitobi-verifyng-api.hf.space/api/payment/callback",
)
FRONTEND_URL = os.getenv("FRONTEND_URL", "https://verifyng-three.vercel.app")

router = APIRouter()


async def initiate_payment(
    amount: int,
    email: str,
    verification_id: str,
) -> dict:
    
    """Initiate payment with Squad API."""
    if not SQUAD_API_KEY:
        raise ValueError("SQUAD_API_KEY environment variable is required")

    url = f"{SQUAD_API_URL}/transaction/initiate"
    headers = {
        "Authorization": f"Bearer {SQUAD_API_KEY}",
        "Content-Type": "application/json",
    }
    transaction_ref = f"VNG-{verification_id}"
    data = {
        "amount": amount,
        "email": email,
        "currency": "NGN",
        "initiate_type": "inline",
        "transaction_ref": transaction_ref,
        "callback_url": _get_payment_callback_url(),
        "metadata": {
            "verification_id": verification_id,
        },
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, headers=headers, json=data, timeout=10.0)
            response.raise_for_status()
            payload = response.json()
            response_data = payload.get("data", {}) if isinstance(payload, dict) else {}
            squad_ref = (
                payload.get("transaction_ref")
                or response_data.get("transaction_ref")
                or response_data.get("reference")
                or transaction_ref
            )
            checkout_url = (
                payload.get("checkout_url")
                or response_data.get("checkout_url")
                or response_data.get("authorization_url")
                or response_data.get("payment_url")
            )

            if checkout_url and isinstance(response_data, dict):
                response_data["checkout_url"] = checkout_url
                payload["data"] = response_data

            if squad_ref:
                create_payment_record(
                    squad_ref=squad_ref,
                    verification_id=verification_id,
                )
            else:
                logger.warning(
                    "Squad initiate response did not include transaction_ref: %s",
                    payload,
                )


            return payload
        except httpx.HTTPStatusError as e:
            logger.error(f"Squad API error: {e.response.status_code} - {e.response.text}")
            raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
        except Exception as e:
            logger.error(f"Error initiating payment: {e}")
            raise HTTPException(status_code=500, detail="Payment initiation failed")


@router.get("/api/payment/callback")
async def payment_callback(
    request: Request,
    background_tasks: BackgroundTasks,
):
    """Handle Squad browser callback after sandbox payment succeeds."""
    transaction_ref = _extract_transaction_ref(dict(request.query_params))
    if not transaction_ref:
        raise HTTPException(status_code=400, detail="Missing transaction_ref")

    verification_id = _queue_paid_verification(transaction_ref, background_tasks)
    return RedirectResponse(
        url=f"{_get_frontend_url()}/results/{verification_id}",
        status_code=307,
    )


@router.post("/api/webhook/squad")
async def squad_webhook_api(
    payload: dict,
    background_tasks: BackgroundTasks,
):
    """Handle Squad server webhook after payment succeeds."""
    transaction_ref = _extract_transaction_ref(payload)
    if not transaction_ref:
        raise HTTPException(status_code=400, detail="Missing transaction_ref")

    verification_id = _queue_paid_verification(transaction_ref, background_tasks)
    return {
        "status": "queued",
        "verification_id": verification_id,
    }


@router.post("/webhook")
async def squad_webhook(
    payload: dict,
    background_tasks: BackgroundTasks,
):
    """Backward-compatible Squad webhook route."""
    return await squad_webhook_api(payload, background_tasks)


def _queue_paid_verification(
    transaction_ref: str,
    background_tasks: BackgroundTasks,
) -> str:
    payment = confirm_payment(transaction_ref)
    if not payment:
        payment = get_payment_by_squad_ref(transaction_ref)

    if not payment:
        verification_id = _verification_id_from_transaction_ref(transaction_ref)
        if verification_id:
            payment = create_payment_record(transaction_ref, verification_id)
            payment = confirm_payment(transaction_ref) or payment

    if not payment:
        logger.error("Payment record not found for %s", transaction_ref)
        raise HTTPException(status_code=404, detail="Payment record not found")

    verification_id = payment.get("verification_id")
    if not verification_id:
        logger.error("No verification_id in payment %s", transaction_ref)
        raise HTTPException(status_code=400, detail="Invalid payment record")

    verification = get_verification_result(verification_id)
    if not verification:
        logger.error("Verification record not found: %s", verification_id)
        raise HTTPException(status_code=404, detail="Verification record not found")

    if verification.get("status") == "COMPLETE":
        return verification_id

    temp_file_path = verification.get("temp_file_path")
    file_url = verification.get("file_url")

    if temp_file_path:
        background_tasks.add_task(
            verify_payment,
            verification_id,
            temp_file_path,
            transaction_ref,
        )
    elif file_url:
        background_tasks.add_task(trigger_ai_pipeline, verification_id)
    else:
        logger.error("No temp_file_path or file_url for %s", verification_id)
        raise HTTPException(status_code=400, detail="File not uploaded")

    return verification_id


def _extract_transaction_ref(payload: dict) -> str | None:
    data = payload.get("data", {}) if isinstance(payload, dict) else {}
    if not isinstance(data, dict):
        data = {}

    return (
        payload.get("transaction_ref")
        or payload.get("reference")
        or payload.get("trxref")
        or payload.get("transactionReference")
        or data.get("transaction_ref")
        or data.get("reference")
        or data.get("trxref")
        or data.get("transactionReference")
    )


def _verification_id_from_transaction_ref(transaction_ref: str) -> str | None:
    if transaction_ref.startswith("VNG-"):
        return transaction_ref.removeprefix("VNG-")
    return None


def _get_payment_callback_url() -> str:
    return os.getenv("WEBHOOK_URL", WEBHOOK_URL)


def _get_frontend_url() -> str:
    return os.getenv("FRONTEND_URL", FRONTEND_URL).rstrip("/")



from pydantic import BaseModel

class InitiatePaymentRequest(BaseModel):
    amount: int
    email: str
    transaction_ref: str

@router.post("/initiate-payment")
async def initiate_payment_endpoint(
    request: InitiatePaymentRequest,
):
    """Endpoint to initiate payment."""
    result = await initiate_payment(request.amount, request.email, request.transaction_ref)

    return result
