import httpx
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from db import get_db
from models import Message
import os
from ai import process_incoming_message
from state import app_state
from routes.sms import SURGE_API_KEY, SURGE_API_URL

router = APIRouter()

class SurgeWebhook(BaseModel):
    phone_number: str
    message_text: str

@router.post("/webhook/surge")
async def webhook_surge(payload: SurgeWebhook, db: Session = Depends(get_db)):
    """
    Receives incoming SMS webhook payload from Surge.
    Stores the payload, optionally processes with AI, and sends a reply.
    """
    # Use Pydantic fields
    phone_number = payload.phone_number
    message_text = payload.message_text

    # 1. Store incoming message in DB
    incoming_message = Message(
        phone_number=phone_number,
        direction="incoming",
        message_text=message_text,
        webhook_payload=payload.dict(),
        status="received"
    )
    db.add(incoming_message)
    db.commit()
    db.refresh(incoming_message)

    # 2. Check if AI Auto-Reply is enabled
    if app_state["auto_reply_enabled"] and message_text:
        # Call Groq AI
        ai_result = process_incoming_message(message_text)
        
        # Update original message with classification
        incoming_message.ai_classification = ai_result.get("classification")
        incoming_message.ai_response = ai_result.get("reply")
        db.commit()

        # Send reply SMS via Surge
        reply_num = phone_number
        reply_body = ai_result.get("reply")

        if reply_body:
            out_payload = {
                "to": reply_num,
                "body": reply_body
            }
            headers = {
                "Authorization": f"Bearer {SURGE_API_KEY}",
                "Content-Type": "application/json"
            }
            
            # Non-blocking background task would be better here, but doing it sync/await inline for simplicity
            try:
                async with httpx.AsyncClient() as client:
                    await client.post(SURGE_API_URL, json=out_payload, headers=headers)
                reply_status = "sent"
            except Exception as e:
                print(f"Auto-reply send failed: {e}")
                reply_status = "failed"
            
            # Log the reply as a new outgoing message
            reply_record = Message(
                phone_number=reply_num,
                direction="outgoing",
                message_text=reply_body,
                status=reply_status,
                ai_classification="auto_reply", # indicate this was generated
            )
            db.add(reply_record)
            db.commit()

    return {
        "status": "received",
        "phone_number": phone_number,
        "message_text": message_text,
        "intent": incoming_message.ai_classification,
        "auto_reply": incoming_message.ai_response
    }
