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
