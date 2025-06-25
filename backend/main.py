from fastapi import FastAPI
from backend.models import ChatRequest, ChatResponse
from backend.agent import run_agent
from backend.calendar_service import JsonCalendarService
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import json

app = FastAPI()

# Allow CORS for local frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

calendar_service = JsonCalendarService()

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    agent_state = run_agent(request.message)
    status = "success" if agent_state.get("booking_confirmed") or agent_state.get("intent") != "book" else "conflict"
    return ChatResponse(
        response=agent_state.get("response", ""),
        status=status,
        alternative_slots=agent_state.get("available_slots") or []
    )

@app.get("/calendar")
async def get_calendar():
    # Return all booked slots
    if not os.path.exists(calendar_service.file_path):
        return JSONResponse(content=[])
    with open(calendar_service.file_path, 'r') as f:
        data = json.load(f)
    return JSONResponse(content=data) 