from fastapi import APIRouter
from pydantic import BaseModel
from state import app_state

router = APIRouter()

class ToggleRequest(BaseModel):
    enabled: bool

@router.post("/toggle-ai")
def toggle_ai(request: ToggleRequest):
    app_state["auto_reply_enabled"] = request.enabled
    return {"status": "success", "auto_reply_enabled": app_state["auto_reply_enabled"]}

@router.get("/toggle-ai")
def get_toggle_ai():
    return {"auto_reply_enabled": app_state["auto_reply_enabled"]}
