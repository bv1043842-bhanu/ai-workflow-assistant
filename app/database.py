"""SQLite database setup and connection helpers for the application."""

from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
import sqlite3


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATABASE_PATH = PROJECT_ROOT / "data" / "events.db"


@contextmanager
def get_connection(database_path: str | Path) -> Generator[sqlite3.Connection, None, None]:
    """Open a SQLite connection and close it when the caller is finished."""
    connection: sqlite3.Connection | None = None

    try:
        connection = sqlite3.connect(database_path)
        connection.row_factory = sqlite3.Row
        yield connection
    finally:
        if connection is not None:
            connection.close()


def initialize_database(database_path: str | Path) -> None:
    """Create the database directory and events table when they do not exist."""
    database_file = Path(database_path)
    database_file.parent.mkdir(parents=True, exist_ok=True)

    with get_connection(database_file) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                event_date TEXT NOT NULL,
                location TEXT NOT NULL
            )
            """
        )
        connection.commit()
