from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json
import os

class CalendarService(ABC):
    @abstractmethod
    def check_availability(self, date: str, start: str, duration: int) -> bool:
        pass

    @abstractmethod
    def get_alternative_slots(self, date: str, duration: int) -> List[Dict]:
        pass

    @abstractmethod
    def book_slot(self, date: str, start: str, end: str, summary: str) -> bool:
        pass

class JsonCalendarService(CalendarService):
    def __init__(self, file_path: str = 'backend/calendar.json'):
        self.file_path = file_path
        if not os.path.exists(self.file_path):
            with open(self.file_path, 'w') as f:
                json.dump([], f)

    def _load(self):
        with open(self.file_path, 'r') as f:
            return json.load(f)

    def _save(self, data):
        with open(self.file_path, 'w') as f:
            json.dump(data, f, indent=2)

    def check_availability(self, date: str, start: str, duration: int) -> bool:
        events = self._load()
        start_dt = datetime.strptime(f"{date} {start}", "%Y-%m-%d %H:%M")
        end_dt = start_dt + timedelta(minutes=duration)
        for event in events:
            event_start = datetime.strptime(f"{event['date']} {event['start']}", "%Y-%m-%d %H:%M")
            event_end = datetime.strptime(f"{event['date']} {event['end']}", "%Y-%m-%d %H:%M")
            if (start_dt < event_end and end_dt > event_start):
                return False
        return True

    def get_alternative_slots(self, date: str, duration: int) -> List[Dict]:
        events = self._load()
        slots = []
        day_start = datetime.strptime(f"{date} 09:00", "%Y-%m-%d %H:%M")
        day_end = datetime.strptime(f"{date} 18:00", "%Y-%m-%d %H:%M")
        current = day_start
        while current + timedelta(minutes=duration) <= day_end:
            slot_start = current
            slot_end = slot_start + timedelta(minutes=duration)
            available = True
            for event in events:
                event_start = datetime.strptime(f"{event['date']} {event['start']}", "%Y-%m-%d %H:%M")
                event_end = datetime.strptime(f"{event['date']} {event['end']}", "%Y-%m-%d %H:%M")
                if (slot_start < event_end and slot_end > event_start):
                    available = False
                    break
            if available:
                slots.append({
                    "date": date,
                    "start": slot_start.strftime("%H:%M"),
                    "end": slot_end.strftime("%H:%M")
                })
            current += timedelta(minutes=30)
        return slots

    def book_slot(self, date: str, start: str, end: str, summary: str) -> bool:
        if not self.check_availability(date, start, (datetime.strptime(end, "%H:%M") - datetime.strptime(start, "%H:%M")).seconds // 60):
            return False
        events = self._load()
        events.append({
            "date": date,
            "start": start,
            "end": end,
            "summary": summary
        })
        self._save(events)
        return True

    def get_conflicting_booking(self, date: str, start: str, duration: int) -> Optional[dict]:
        events = self._load()
        start_dt = datetime.strptime(f"{date} {start}", "%Y-%m-%d %H:%M")
        end_dt = start_dt + timedelta(minutes=duration)
        for event in events:
            event_start = datetime.strptime(f"{event['date']} {event['start']}", "%Y-%m-%d %H:%M")
            event_end = datetime.strptime(f"{event['date']} {event['end']}", "%Y-%m-%d %H:%M")
            if (start_dt < event_end and end_dt > event_start):
                return event
        return None 