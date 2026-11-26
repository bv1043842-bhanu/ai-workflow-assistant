"""SQLite CRUD operations for campus events."""

from datetime import date
from pathlib import Path
from typing import Any, Mapping

from app.database import get_connection


def _row_to_event(row: Any) -> dict[str, Any]:
    """Convert a SQLite row into the event data used by the API."""
    return {
        "id": row["id"],
        "title": row["title"],
        "description": row["description"],
        "date": date.fromisoformat(row["event_date"]),
        "location": row["location"],
    }


def create_event(
    database_path: str | Path, event_data: Mapping[str, Any]
) -> dict[str, Any]:
    """Insert an event and return its stored data, including its new ID."""
    event_date: date = event_data["date"]

    with get_connection(database_path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO events (title, description, event_date, location)
            VALUES (?, ?, ?, ?)
            """,
            (
                event_data["title"],
                event_data["description"],
                event_date.isoformat(),
                event_data["location"],
            ),
        )
        connection.commit()

    return {
        "id": cursor.lastrowid,
        "title": event_data["title"],
        "description": event_data["description"],
        "date": event_date,
        "location": event_data["location"],
    }


def list_events(database_path: str | Path) -> list[dict[str, Any]]:
    """Return all events in ascending ID order."""
    with get_connection(database_path) as connection:
        rows = connection.execute(
            """
            SELECT id, title, description, event_date, location
            FROM events
            ORDER BY id
            """
        ).fetchall()

    return [_row_to_event(row) for row in rows]


def get_event(database_path: str | Path, event_id: int) -> dict[str, Any] | None:
    """Return one event, or None when its ID does not exist."""
    with get_connection(database_path) as connection:
        row = connection.execute(
            """
            SELECT id, title, description, event_date, location
            FROM events
            WHERE id = ?
            """,
            (event_id,),
        ).fetchone()

    if row is None:
        return None

    return _row_to_event(row)


def update_event(
    database_path: str | Path, event_id: int, event_data: Mapping[str, Any]
) -> dict[str, Any] | None:
    """Update an event and return it, or None when its ID does not exist."""
    event_date: date = event_data["date"]

    with get_connection(database_path) as connection:
        cursor = connection.execute(
            """
            UPDATE events
            SET title = ?, description = ?, event_date = ?, location = ?
            WHERE id = ?
            """,
            (
                event_data["title"],
                event_data["description"],
                event_date.isoformat(),
                event_data["location"],
                event_id,
            ),
        )
        connection.commit()

    if cursor.rowcount == 0:
        return None

    return get_event(database_path, event_id)


def delete_event(database_path: str | Path, event_id: int) -> bool:
    """Delete an event and report whether an event was deleted."""
    with get_connection(database_path) as connection:
        cursor = connection.execute(
            "DELETE FROM events WHERE id = ?",
            (event_id,),
        )
        connection.commit()

    return cursor.rowcount > 0
