from datetime import date

from fastapi import FastAPI, HTTPException, status
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


@app.get("/events/{event_id}", response_model=Event)
def get_event(event_id: int):
    for event in events:
        if event.id == event_id:
            return event

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Event with ID {event_id} not found",
    )


@app.put("/events/{event_id}", response_model=Event)
def update_event(event_id: int, event: EventCreate):
    for index, existing_event in enumerate(events):
        if existing_event.id == event_id:
            updated_event = Event(id=event_id, **event.model_dump())
            events[index] = updated_event
            return updated_event

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Event with ID {event_id} not found",
    )
