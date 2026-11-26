from datetime import date

from fastapi import FastAPI, status
from pydantic import BaseModel

app = FastAPI()


class EventCreate(BaseModel):
    title: str
    description: str
    date: date
    location: str


class Event(EventCreate):
    id: int


events: list[Event] = []
next_event_id = 1


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "message": "AI Workflow Assistant backend is running",
    }


@app.post("/events", response_model=Event, status_code=status.HTTP_201_CREATED)
def create_event(event: EventCreate):
    global next_event_id

    created_event = Event(id=next_event_id, **event.model_dump())
    events.append(created_event)
    next_event_id += 1

    return created_event


@app.get("/events", response_model=list[Event])
def list_events():
    return events
