from __future__ import annotations

from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_event_ingest_and_decide_flow() -> None:
    event_payload = {
        "user_id": "u_001",
        "session_id": "s_001",
        "event_type": "click",
        "event_time": datetime.now(timezone.utc).isoformat(),
        "attributes": {"label": "discount_banner"},
    }

    ingest_response = client.post("/api/v1/events", json=event_payload)
    assert ingest_response.status_code == 201
    assert ingest_response.json()["status"] == "accepted"

    decide_payload = {
        "user_id": "u_001",
        "session_id": "s_001",
        "page_type": "home",
        "context": {"device": "web"},
    }

    decide_response = client.post("/api/v1/personalization/decide", json=decide_payload)
    assert decide_response.status_code == 200
    body = decide_response.json()
    assert body["trace_id"].startswith("trc_")
    assert len(body["recommendations"]) > 0
    assert "segment" in body


def test_profile_and_trace_lookup() -> None:
    decide_payload = {
        "user_id": "u_002",
        "session_id": "s_002",
        "page_type": "plp",
        "context": {},
    }
    decide_response = client.post("/api/v1/personalization/decide", json=decide_payload)
    trace_id = decide_response.json()["trace_id"]

    profile_response = client.get("/api/v1/users/u_002/profile")
    assert profile_response.status_code == 200
    assert profile_response.json()["last_trace_id"] == trace_id

    trace_response = client.get(f"/api/v1/traces/{trace_id}")
    assert trace_response.status_code == 200
    assert trace_response.json()["status"] == "ok"


def test_missing_trace_returns_404() -> None:
    response = client.get("/api/v1/traces/non_existent")
    assert response.status_code == 404
