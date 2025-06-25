from langgraph.graph import StateGraph, END
from dateutil import parser as date_parser
from typing import Dict, Any
from backend.models import AgentState
from backend.calendar_service import JsonCalendarService
import re

calendar_service = JsonCalendarService()

def input_node(state: AgentState) -> AgentState:
    return state

def intent_detection_node(state: AgentState) -> AgentState:
    text = state.user_input.lower()
    if any(word in text for word in ["book", "schedule", "reserve"]):
        state.intent = "book"
    elif any(word in text for word in ["available", "free", "slots", "open"]):
        state.intent = "query"
    else:
        state.intent = "other"
    return state

def time_extraction_node(state: AgentState) -> AgentState:
    # Try to extract date/time using dateutil and regex for duration
    text = state.user_input
    try:
        dt = date_parser.parse(text, fuzzy=True)
        # Look for duration in minutes (e.g., "for 1 hour", "60 minutes")
        duration = 60  # default
        match = re.search(r"(\d+)\s*(minutes|min|hours|hour)", text, re.I)
        if match:
            val = int(match.group(1))
            if "hour" in match.group(2):
                duration = val * 60
            else:
                duration = val
        state.extracted_time = {
            "date": dt.strftime("%Y-%m-%d"),
            "start": dt.strftime("%H:%M"),
            "duration": duration
        }
    except Exception:
        state.extracted_time = None
    return state

def availability_check_node(state: AgentState) -> AgentState:
    if not state.extracted_time:
        state.available_slots = []
        return state
    date = state.extracted_time["date"]
    start = state.extracted_time["start"]
    duration = state.extracted_time["duration"]
    available = calendar_service.check_availability(date, start, duration)
    if available:
        state.available_slots = []
    else:
        state.available_slots = calendar_service.get_alternative_slots(date, duration)
    return state

def booking_node(state: AgentState) -> AgentState:
    if state.intent != "book" or not state.extracted_time:
        state.booking_confirmed = False
        return state
    date = state.extracted_time["date"]
    start = state.extracted_time["start"]
    duration = state.extracted_time["duration"]
    # Calculate end time
    from datetime import datetime, timedelta
    start_dt = datetime.strptime(f"{date} {start}", "%Y-%m-%d %H:%M")
    end_dt = start_dt + timedelta(minutes=duration)
    end = end_dt.strftime("%H:%M")
    summary = state.user_input
    confirmed = calendar_service.book_slot(date, start, end, summary)
    state.booking_confirmed = confirmed
    return state

def response_node(state: AgentState) -> AgentState:
    if state.intent == "query":
        if state.available_slots:
            slots = ", ".join([f"{s['start']}-{s['end']}" for s in state.available_slots])
            state.response = f"Available slots: {slots}"
        else:
            state.response = "No available slots found."
    elif state.intent == "book":
        if state.booking_confirmed:
            t = state.extracted_time
            state.response = f"I've booked your appointment for {t['date']} at {t['start']}. Anything else I can help with?"
        else:
            # Try to get the conflicting booking and include its summary
            t = state.extracted_time
            conflicting = None
            if t:
                conflicting = calendar_service.get_conflicting_booking(t['date'], t['start'], t['duration'])
            if conflicting:
                summary = conflicting.get('summary', 'another event')
                state.response = (
                    f"There is already a booking at {conflicting['start']} on {conflicting['date']}: {summary}. "
                    f"Would you like to choose another time?"
                )
                if state.available_slots:
                    alt = state.available_slots
                    slot_str = ", ".join([f"{s['start']}-{s['end']}" for s in alt])
                    state.response += f" Suggested alternatives: {slot_str}."
            elif state.available_slots:
                alt = state.available_slots
                slot_str = ", ".join([f"{s['start']}-{s['end']}" for s in alt])
                state.response = f"That slot is unavailable. Would you like {slot_str}?"
            else:
                state.response = "That slot is unavailable and no alternatives were found."
    else:
        state.response = "Sorry, I didn't understand your request."
    return state

# Build the LangGraph state machine
graph = StateGraph(AgentState)
graph.add_node("input", input_node)
graph.add_node("intent_detection", intent_detection_node)
graph.add_node("time_extraction", time_extraction_node)
graph.add_node("availability_check", availability_check_node)
graph.add_node("booking", booking_node)
graph.add_node("respond", response_node)

graph.set_entry_point("input")
graph.add_edge("input", "intent_detection")
graph.add_edge("intent_detection", "time_extraction")
graph.add_edge("time_extraction", "availability_check")
graph.add_edge("availability_check", "booking")
graph.add_edge("booking", "respond")
graph.add_edge("respond", END)

agent_executor = graph.compile()

def run_agent(user_input: str) -> dict:
    state = AgentState(user_input=user_input)
    result = agent_executor.invoke(state)
    # Convert to dict if not already
    if hasattr(result, 'dict'):
        return result.dict()
    return dict(result) 