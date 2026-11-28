
import pytest
import httpx
from types import SimpleNamespace
from fastapi.testclient import TestClient

from app.main import create_app


INVALID_TEXT_FIELD_CASES = [
    ("title", ""),
    ("description", ""),
    ("location", ""),
    ("title", "   "),
    ("description", "   "),
    ("location", "   "),
]


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


@pytest.mark.parametrize(("field", "invalid_value"), INVALID_TEXT_FIELD_CASES)
def test_create_event_rejects_blank_text_fields(client, field, invalid_value):
    event_data = {
        "title": "Spring Festival",
        "description": "An outdoor campus festival.",
        "date": "2026-04-12",
        "location": "Main Quad",
    }
    event_data[field] = invalid_value

    response = client.post("/events", json=event_data)

    assert response.status_code == 422


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


def _create_pagination_test_events(client, count=12):
    events = [
        {
            "title": f"Event {index}",
            "description": f"Description {index}",
            "date": "2026-04-12" if index % 2 else "2026-04-13",
            "location": "Main Quad" if index % 2 else "Student Center",
        }
        for index in range(1, count + 1)
    ]

    for event in events:
        client.post("/events", json=event)

    return events


def test_list_events_uses_default_pagination_and_id_order(client):
    events = _create_pagination_test_events(client)

    response = client.get("/events")

    assert response.status_code == 200
    assert response.json() == [
        {"id": index, **event} for index, event in enumerate(events[:10], start=1)
    ]


def test_list_events_applies_skip_and_limit_in_id_order(client):
    events = _create_pagination_test_events(client)

    response = client.get("/events", params={"skip": 3, "limit": 4})

    assert response.status_code == 200
    assert response.json() == [
        {"id": index, **event}
        for index, event in enumerate(events[3:7], start=4)
    ]


@pytest.mark.parametrize(
    ("params", "expected_count"),
    [
        ({"skip": 0, "limit": 1}, 1),
        ({"skip": 0, "limit": 100}, 12),
    ],
)
def test_list_events_accepts_pagination_boundaries(client, params, expected_count):
    _create_pagination_test_events(client)

    response = client.get("/events", params=params)

    assert response.status_code == 200
    assert len(response.json()) == expected_count


@pytest.mark.parametrize(
    "params",
    [
        {"skip": -1},
        {"limit": 0},
        {"limit": 101},
        {"skip": "not-an-integer"},
        {"limit": "not-an-integer"},
    ],
)
def test_list_events_rejects_invalid_pagination_values(client, params):
    response = client.get("/events", params=params)

    assert response.status_code == 422


def test_list_events_returns_empty_list_when_skip_exceeds_available_events(client):
    _create_pagination_test_events(client, count=2)

    response = client.get("/events", params={"skip": 2})

    assert response.status_code == 200
    assert response.json() == []


def test_list_events_combines_pagination_with_filters(client):
    events = _create_pagination_test_events(client)

    response = client.get(
        "/events",
        params={
            "title": "event",
            "location": "main quad",
            "date": "2026-04-12",
            "skip": 1,
            "limit": 2,
        },
    )

    assert response.status_code == 200
    assert response.json() == [
        {"id": 3, **events[2]},
        {"id": 5, **events[4]},
    ]


def _create_filter_test_events(client):
    events = [
        {
            "title": "Spring Festival",
            "description": "An outdoor campus festival.",
            "date": "2026-04-12",
            "location": "Main Quad",
        },
        {
            "title": "Spring Career Fair",
            "description": "Meet employers on campus.",
            "date": "2026-04-12",
            "location": "Student Center",
        },
        {
            "title": "Winter Festival",
            "description": "A winter campus celebration.",
            "date": "2026-12-01",
            "location": "Main Quad",
        },
    ]

    for event in events:
        client.post("/events", json=event)

    return events


def test_list_events_filters_by_partial_case_insensitive_title(client):
    events = _create_filter_test_events(client)

    response = client.get("/events", params={"title": "RING FES"})

    assert response.status_code == 200
    assert response.json() == [{"id": 1, **events[0]}]


def test_list_events_filters_by_partial_case_insensitive_location(client):
    events = _create_filter_test_events(client)

    response = client.get("/events", params={"location": "QUA"})

    assert response.status_code == 200
    assert response.json() == [
        {"id": 1, **events[0]},
        {"id": 3, **events[2]},
    ]


def test_list_events_filters_by_exact_date(client):
    events = _create_filter_test_events(client)

    response = client.get("/events", params={"date": "2026-04-12"})

    assert response.status_code == 200
    assert response.json() == [
        {"id": 1, **events[0]},
        {"id": 2, **events[1]},
    ]


def test_list_events_combines_filters_with_and_behavior(client):
    events = _create_filter_test_events(client)

    response = client.get(
        "/events",
        params={
            "title": "festival",
            "location": "quad",
            "date": "2026-04-12",
        },
    )

    assert response.status_code == 200
    assert response.json() == [{"id": 1, **events[0]}]


def test_list_events_returns_empty_list_when_no_events_match(client):
    _create_filter_test_events(client)

    response = client.get("/events", params={"title": "hackathon"})

    assert response.status_code == 200
    assert response.json() == []


def test_list_events_rejects_invalid_date_filter(client):
    response = client.get("/events", params={"date": "not-a-date"})

    assert response.status_code == 422


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


@pytest.mark.parametrize(("field", "invalid_value"), INVALID_TEXT_FIELD_CASES)
def test_update_event_rejects_blank_text_fields(client, field, invalid_value):
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
    updated_event_data[field] = invalid_value

    response = client.put("/events/1", json=updated_event_data)

    assert response.status_code == 422


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


def test_ask_ai_returns_answer_using_available_events(client, monkeypatch):
    event_data = {
        "title": "Spring Festival",
        "description": "An outdoor campus festival.",
        "date": "2026-04-12",
        "location": "Main Quad",
    }

    client.post("/events", json=event_data)

    fake_response = SimpleNamespace(
        message=SimpleNamespace(
            content="Spring Festival is scheduled for 2026-04-12 at Main Quad."
        )
    )

    monkeypatch.setattr(
        "app.main.ollama.chat",
        lambda **kwargs: fake_response,
    )

    response = client.post(
        "/ai/ask",
        json={"question": "When is the Spring Festival?"},
    )

    assert response.status_code == 200
    assert response.json()["answer"] == (
        "Spring Festival is scheduled for 2026-04-12 at Main Quad."
    )
    assert response.json()["events_used"] == 1


def test_ask_ai_returns_message_when_no_events_exist(client, monkeypatch):
    def fail_if_ollama_is_called(**kwargs):
        pytest.fail("Ollama should not be called when no events exist")

    monkeypatch.setattr(
        "app.main.ollama.chat",
        fail_if_ollama_is_called,
    )

    response = client.post(
        "/ai/ask",
        json={"question": "What campus events are available?"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "answer": "No campus events are currently available.",
        "events_used": 0,
    }


def test_ask_ai_returns_503_when_ollama_is_unavailable(client, monkeypatch):
    event_data = {
        "title": "Spring Festival",
        "description": "An outdoor campus festival.",
        "date": "2026-04-12",
        "location": "Main Quad",
    }

    create_response = client.post("/events", json=event_data)
    assert create_response.status_code == 201

    def raise_connection_error(**kwargs):
        raise httpx.ConnectError("Connection refused")

    monkeypatch.setattr(
        "app.main.ollama.chat",
        raise_connection_error,
    )

    response = client.post(
        "/ai/ask",
        json={"question": "What campus events are available?"},
    )

    assert response.status_code == 503
    assert response.json() == {
        "detail": "Cannot connect to Ollama. Make sure Ollama is running."
    }
