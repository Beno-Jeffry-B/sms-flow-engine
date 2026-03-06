from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from datetime import datetime
from db import Base

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String, index=True)
    direction = Column(String)  # "incoming" or "outgoing"
    message_text = Column(Text)
    ai_classification = Column(String, nullable=True)
    ai_response = Column(Text, nullable=True)
    webhook_payload = Column(JSON, nullable=True)
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
