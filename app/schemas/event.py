from datetime import date, time
from typing import Optional

from pydantic import BaseModel

from app.models.event import EventType

class EventResponse(BaseModel):
    id: str
    title: str
    event_date: date
    event_time: Optional[time] = None
    event_type: EventType
    department_id: Optional[str] = None

    class Config:
        from_attributes = True
