import logging
import os
from typing import Optional

import httpx
from fastapi import APIRouter, HTTPException

from .database import get_payment_by_squad_ref, get_verification_result, confirm_payment, create_payment_record
from .verifications import verify_payment
from .pipeline import trigger_ai_pipeline

logger = logging.getLogger(__name__)

SQUAD_API_URL = os.getenv("SQUAD_API_URL", "https://sandbox-api-d.squadco.com")
SQUAD_API_KEY = os.getenv("SQUAD_API_KEY")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://your-domain.com/webhook")  # Set this to your actual webhook URL

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
    data = {
        "amount": amount,
        "email": email,
        "currency": "NGN",
        "initiate_type": "inline",
        # "transaction_ref": transaction_ref,
        # "callback_url": WEBHOOK_URL,
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, headers=headers, json=data)
            response.raise_for_status()
            payload = response.json()
            response_data = payload.get("data", {}) if isinstance(payload, dict) else {}
            squad_ref = (
                payload.get("transaction_ref")
                or response_data.get("transaction_ref")
                or response_data.get("reference")
            )

            if not squad_ref:
                raise ValueError("Squad response did not include a transaction_ref")

            create_payment_record( 
                squad_ref=squad_ref,
                verification_id=verification_id,
             )


            return payload
        except httpx.HTTPStatusError as e:
            logger.error(f"Squad API error: {e.response.status_code} - {e.response.text}")
            raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
        except Exception as e:
            logger.error(f"Error initiating payment: {e}")
            raise HTTPException(status_code=500, detail="Payment initiation failed")


@router.post("/webhook")
async def squad_webhook(payload: dict):
    """Handle webhook from Squad after payment."""
    transaction_ref = payload.get("transaction_ref")
    if not transaction_ref:
        raise HTTPException(status_code=400, detail="Missing transaction_ref")

    # Verify transaction with Squad
    verify_url = f"{SQUAD_API_URL}/transaction/verify/{transaction_ref}"
    headers = {"Authorization": f"Bearer {SQUAD_API_KEY}"}

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(verify_url, headers=headers)
            response.raise_for_status()
            verify_data = response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Squad verify error: {e.response.status_code} - {e.response.text}")
            raise HTTPException(status_code=500, detail="Transaction verification failed")
        except Exception as e:
            logger.error(f"Error verifying transaction: {e}")
            raise HTTPException(status_code=500, detail="Transaction verification failed")

    # Check if payment was successful
    if verify_data.get("status") != "success":
        logger.info(f"Payment not successful for {transaction_ref}: {verify_data}")
        return {"status": "payment_not_successful"}

    # Confirm payment in our database
    payment = confirm_payment(transaction_ref)
    if not payment:
        logger.error(f"Payment record not found for {transaction_ref}")
        raise HTTPException(status_code=404, detail="Payment record not found")

    verification_id = payment.get("verification_id")
    if not verification_id:
        logger.error(f"No verification_id in payment {transaction_ref}")
        raise HTTPException(status_code=400, detail="Invalid payment record")

    # Get verification details
    verification = get_verification_result(verification_id)
    if not verification:
        logger.error(f"Verification record not found: {verification_id}")
        raise HTTPException(status_code=404, detail="Verification record not found")

    temp_file_path = verification.get("temp_file_path")
    if not temp_file_path:
        logger.error(f"No temp_file_path for verification {verification_id}")
        raise HTTPException(status_code=400, detail="File not uploaded")

    # Now proceed with file upload and AI pipeline
    try:
        await verify_payment(verification_id, temp_file_path, transaction_ref)
    except Exception as e:
        logger.error(f"Error in verify_payment: {e}")
        raise HTTPException(status_code=500, detail="Verification process failed")
    
    try:
        await trigger_ai_pipeline(verification_id)
    except Exception as e:
        logger.error(f"Error triggering AI pipeline: {e}")
        raise HTTPException(status_code=500, detail="AI pipeline trigger failed")



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
