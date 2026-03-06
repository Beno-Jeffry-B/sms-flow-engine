import os
from groq import Groq
from sqlalchemy.orm import Session
from sqlalchemy import desc
from models import Message

# Initialize Groq client
groq_api_key = os.getenv("GROQ_API_KEY", "")
client = Groq(api_key=groq_api_key)

def generate_ai_reply(phone_number: str, text: str, db: Session) -> str:
    """
    Calls Groq to generate a conversational reply based on DB history.
    """
    if not groq_api_key:
        return "Error: GROQ_API_KEY is not configured."

    # Fetch last 10 messages for context, oldest first
    history = db.query(Message).filter(Message.phone_number == phone_number).order_by(desc(Message.created_at)).limit(10).all()
    history.reverse()

    messages = [
        {"role": "system", "content": "You are a helpful SMS customer support assistant. Keep replies concise, friendly, and helpful."}
    ]

    for msg in history:
        # Don't duplicate the current incoming message if it was already saved
        if msg.message_text == text and msg.direction == "incoming" and msg == history[-1]:
            continue
            
        role = "user" if msg.direction == "incoming" else "assistant"
        if msg.message_text:
            messages.append({"role": role, "content": msg.message_text})

    messages.append({"role": "user", "content": text})

    try:
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",  # Fast and robust model
            messages=messages,
            temperature=0.6,
            max_tokens=150
        )
        return completion.choices[0].message.content
        
    except Exception as e:
        print(f"Error calling Groq conversational AI: {e}")
        return "Error processing conversational message via AI."
