import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def client(tmp_path):
    test_app = create_app(tmp_path / "events_test.db")

    with TestClient(test_app) as test_client:
        yield test_client


def test_health_check_returns_expected_response(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "message": "AI Workflow Assistant backend is running",
    }


def test_create_event_returns_created_event(client):
    event_data = {
        "title": "Spring Festival",
        "description": "An outdoor campus festival.",
        "date": "2026-04-12",
        "location": "Main Quad",
    }

    response = client.post("/events", json=event_data)

    assert response.status_code == 201
    assert response.json() == {"id": 1, **event_data}


def test_list_events_returns_created_events(client):
    event_data = {
        "title": "Career Fair",
        "description": "Meet employers on campus.",
        "date": "2026-05-01",
        "location": "Student Center",
    }
    client.post("/events", json=event_data)

    response = client.get("/events")

    assert response.status_code == 200
    assert response.json() == [{"id": 1, **event_data}]


def test_get_event_returns_existing_event(client):
    event_data = {
        "title": "Guest Lecture",
        "description": "A lecture from an industry expert.",
        "date": "2026-06-10",
        "location": "Engineering Hall",
    }
    client.post("/events", json=event_data)

    response = client.get("/events/1")

    assert response.status_code == 200
    assert response.json() == {"id": 1, **event_data}


def test_get_event_returns_not_found_for_nonexistent_event(client):
    response = client.get("/events/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Event with ID 999 not found"}


def test_update_event_returns_updated_event(client):
    original_event_data = {
        "title": "Guest Lecture",
        "description": "A lecture from an industry expert.",
        "date": "2026-06-10",
        "location": "Engineering Hall",
    }
    updated_event_data = {
        "title": "Alumni Panel",
        "description": "Graduates share career advice.",
        "date": "2026-07-15",
        "location": "Auditorium",
    }
    client.post("/events", json=original_event_data)

    response = client.put("/events/1", json=updated_event_data)

    assert response.status_code == 200
    assert response.json() == {"id": 1, **updated_event_data}


def test_update_event_returns_not_found_for_nonexistent_event(client):
    event_data = {
        "title": "Alumni Panel",
        "description": "Graduates share career advice.",
        "date": "2026-07-15",
        "location": "Auditorium",
    }

    response = client.put("/events/999", json=event_data)

    assert response.status_code == 404
    assert response.json() == {"detail": "Event with ID 999 not found"}


def test_delete_event_returns_no_content_and_removes_event(client):
    event_data = {
        "title": "Campus Concert",
        "description": "An evening concert.",
        "date": "2026-08-20",
        "location": "Main Quad",
    }
    client.post("/events", json=event_data)

    response = client.delete("/events/1")

    assert response.status_code == 204
    assert response.content == b""

    get_response = client.get("/events/1")
    assert get_response.status_code == 404
    assert get_response.json() == {"detail": "Event with ID 1 not found"}


def test_delete_event_returns_not_found_for_nonexistent_event(client):
    response = client.delete("/events/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Event with ID 999 not found"}


def test_events_persist_between_app_instances(tmp_path):
    database_path = tmp_path / "events_test.db"
    event_data = {
        "title": "Research Symposium",
        "description": "Students present research projects.",
        "date": "2026-09-10",
        "location": "Library Auditorium",
    }

    with TestClient(create_app(database_path)) as first_client:
        create_response = first_client.post("/events", json=event_data)

    assert create_response.status_code == 201

    with TestClient(create_app(database_path)) as second_client:
        get_response = second_client.get("/events/1")

    assert get_response.status_code == 200
    assert get_response.json() == {"id": 1, **event_data}
