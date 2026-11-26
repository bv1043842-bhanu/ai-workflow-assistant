import pytest
from fastapi.testclient import TestClient

import app.main as main


client = TestClient(main.app)


@pytest.fixture(autouse=True)
def reset_event_store():
    main.events.clear()
    main.next_event_id = 1


def test_health_check_returns_expected_response():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "message": "AI Workflow Assistant backend is running",
    }


def test_create_event_returns_created_event():
    event_data = {
        "title": "Spring Festival",
        "description": "An outdoor campus festival.",
        "date": "2026-04-12",
        "location": "Main Quad",
    }

    response = client.post("/events", json=event_data)

    assert response.status_code == 201
    assert response.json() == {"id": 1, **event_data}


def test_list_events_returns_created_events():
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


def test_get_event_returns_existing_event():
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


def test_get_event_returns_not_found_for_nonexistent_event():
    response = client.get("/events/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Event with ID 999 not found"}


def test_update_event_returns_updated_event():
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


def test_update_event_returns_not_found_for_nonexistent_event():
    event_data = {
        "title": "Alumni Panel",
        "description": "Graduates share career advice.",
        "date": "2026-07-15",
        "location": "Auditorium",
    }

    response = client.put("/events/999", json=event_data)

    assert response.status_code == 404
    assert response.json() == {"detail": "Event with ID 999 not found"}


def test_delete_event_returns_no_content_and_removes_event():
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


def test_delete_event_returns_not_found_for_nonexistent_event():
    response = client.delete("/events/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Event with ID 999 not found"}
