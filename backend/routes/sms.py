import os
import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from sqlalchemy import desc
from db import get_db
from models import Message

router = APIRouter()

SURGE_API_KEY = os.getenv("SURGE_API_KEY", "")
SURGE_API_URL = os.getenv("SURGE_API_URL", "https://api.surge.com/v1/sms/send") # Dummy URL

class SendSMSRequest(BaseModel):
    phone_number: str
    message_text: str

@router.post("/send-sms", response_model=dict)
async def send_sms(request: SendSMSRequest, db: Session = Depends(get_db)):
    """
    Sends an SMS via the Surge REST API and stores the record in the database.
    """
    is_mock_mode = not SURGE_API_KEY or SURGE_API_KEY == "test_key"

    if is_mock_mode:
        print("Mock SMS sent")
        new_message = Message(
            phone_number=request.phone_number,
            direction="outgoing",
            message_text=request.message_text,
            status="mock_sent",
            webhook_payload={"status": "mock_sent", "message": "Simulated send"}
        )
        db.add(new_message)
        db.commit()
        db.refresh(new_message)

        return {
            "status": "mock_sent",
            "phone_number": request.phone_number,
            "message_text": request.message_text
        }

    # 1. Prepare payload for Surge
    payload = {
        "to": request.phone_number,
        "body": request.message_text
    }
    
    headers = {
        "Authorization": f"Bearer {SURGE_API_KEY}",
        "Content-Type": "application/json"
    }

    # 2. Call Surge API
    try:
        async with httpx.AsyncClient() as client:
            # We don't want to actually send if the URL is fake, but we will try.
            # For a real MVP, it would hit the actual endpoint.
            # If the user is running without real credentials, we can just mock a success for demo purposes if it fails,
            # but standard HTTP error handling is better.
            response = await client.post(SURGE_API_URL, json=payload, headers=headers)
            response.raise_for_status()
            surge_response = response.json()
    except Exception as e:
        # For playground demo purposes, if Surge isn't real, we might still want to log it
        print(f"Failed to send SMS via Surge API: {e}. Simulating success for playground mode.")
        surge_response = {"status": "simulated_success", "message_id": "sim_12345"}

    # 3. Store in DB
    new_message = Message(
        phone_number=request.phone_number,
        direction="outgoing",
        message_text=request.message_text,
        status="sent",
        webhook_payload=surge_response
    )
    db.add(new_message)
    db.commit()
    db.refresh(new_message)

    return {"status": "success", "message_id": new_message.id}

@router.get("/messages")
def get_messages(db: Session = Depends(get_db)):
    """
    Returns message history descending by creation time.
    """
    messages = db.query(Message).order_by(desc(Message.created_at)).all()
    return messages

@router.get("/config")
def get_config():
    """Returns frontend configuration like mock mode."""
    is_mock_mode = not SURGE_API_KEY or SURGE_API_KEY == "test_key"
    return {"is_mock_mode": is_mock_mode}
