import httpx
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from db import get_db
from models import Message
import os
from routes.sms import SURGE_API_KEY, SURGE_API_URL

router = APIRouter()

class SurgeWebhook(BaseModel):
    phone_number: str
    message_text: str

def classify_message(text: str) -> str:
    msg = text.lower()
    
    pricing_keywords = ["price", "pricing", "cost", "plan", "subscription"]
    support_keywords = ["help", "issue", "problem", "support", "not working"]
    
    if any(k in msg for k in pricing_keywords):
        return "pricing_query"
        
    if any(k in msg for k in support_keywords):
        return "support_request"
        
    if "?" in msg:
        return "general_question"
        
    return "other"

def generate_reply(intent: str):
    if intent == "pricing_query":
        return "Thanks for your interest! Pricing starts at $9/month."
        
    if intent == "support_request":
        return "Support team will assist you shortly."
        
    if intent == "general_question":
        return "Thanks for reaching out. We'll respond soon."
        
    return None

@router.post("/webhook/surge")
async def webhook_surge(payload: SurgeWebhook, db: Session = Depends(get_db)):
    """
    Receives incoming SMS webhook payload from Surge.
    Stores the payload, processes with AI, and sends a reply.
    """
    # Use Pydantic fields
    phone_number = payload.phone_number
    message_text = payload.message_text

    intent = classify_message(message_text)
    reply = generate_reply(intent)

    # 1. Store incoming message in DB
    incoming_message = Message(
        phone_number=phone_number,
        direction="incoming",
        message_text=message_text,
        ai_classification=intent,
        ai_response=reply,
        webhook_payload=payload.dict(),
        status="received"
    )
    db.add(incoming_message)
    db.commit()
    db.refresh(incoming_message)

    # 2. Auto-send reply SMS
    if reply:
        out_payload = {
            "to": phone_number,
            "body": reply
        }
        headers = {
            "Authorization": f"Bearer {SURGE_API_KEY}",
            "Content-Type": "application/json"
        }
        
        is_mock_mode = not SURGE_API_KEY or SURGE_API_KEY == "test_key"
        
        if is_mock_mode:
            print("Mock auto-reply SMS sent")
            reply_status = "mock_sent"
        else:
            try:
                async with httpx.AsyncClient() as client:
                    await client.post(SURGE_API_URL, json=out_payload, headers=headers)
                reply_status = "sent"
            except Exception as e:
                print(f"Auto-reply send failed: {e}")
                reply_status = "failed"
        
        # Log the reply as a new outgoing message
        reply_record = Message(
            phone_number=phone_number,
            direction="outgoing",
            message_text=reply,
            status=reply_status,
            ai_classification="auto_reply", # indicate this was generated
        )
        db.add(reply_record)
        db.commit()

    return {
        "status": "received",
        "phone_number": phone_number,
        "message_text": message_text,
        "intent": intent,
        "auto_reply": reply
    }
