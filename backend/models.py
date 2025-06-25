from typing import Optional, List, Dict
from pydantic import BaseModel

class AgentState(BaseModel):
    user_input: str
    intent: Optional[str] = None
    extracted_time: Optional[dict] = None
    available_slots: Optional[List[dict]] = None
    booking_confirmed: bool = False
    response: str = ""

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str
    status: str
    alternative_slots: Optional[List[Dict]] = [] 