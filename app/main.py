from datetime import date
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel

from app.database import DEFAULT_DATABASE_PATH, initialize_database
from app.event_repository import (
    create_event as create_event_in_database,
    delete_event as delete_event_in_database,
    get_event as get_event_from_database,
    list_events as list_events_from_database,
    update_event as update_event_in_database,
)


class EventCreate(BaseModel):
    title: str
    description: str
    date: date
    location: str


class Event(EventCreate):
    id: int


def create_app(database_path: str | Path = DEFAULT_DATABASE_PATH) -> FastAPI:
    @asynccontextmanager
    async def lifespan(_: FastAPI):
        initialize_database(database_path)
        yield

    app = FastAPI(lifespan=lifespan)

    @app.get("/health")
    def health_check():
        return {
            "status": "healthy",
            "message": "AI Workflow Assistant backend is running",
        }

    @app.post("/events", response_model=Event, status_code=status.HTTP_201_CREATED)
    def create_event(event: EventCreate):
        created_event = create_event_in_database(database_path, event.model_dump())
        return Event(**created_event)

    @app.get("/events", response_model=list[Event])
    def list_events():
        events = list_events_from_database(database_path)
        return [Event(**event) for event in events]

    @app.get("/events/{event_id}", response_model=Event)
    def get_event(event_id: int):
        event = get_event_from_database(database_path, event_id)

        if event is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Event with ID {event_id} not found",
            )

        return Event(**event)

    @app.put("/events/{event_id}", response_model=Event)
    def update_event(event_id: int, event: EventCreate):
        updated_event = update_event_in_database(
            database_path, event_id, event.model_dump()
        )

        if updated_event is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Event with ID {event_id} not found",
            )

        return Event(**updated_event)

    @app.delete("/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
    def delete_event(event_id: int):
        deleted = delete_event_in_database(database_path, event_id)

        if deleted:
            return

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event with ID {event_id} not found",
        )

    return app


app = create_app()
