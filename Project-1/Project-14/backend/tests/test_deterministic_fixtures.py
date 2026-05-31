from __future__ import annotations

from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _ingest(user_id: str, label: str) -> None:
    response = client.post(
        "/api/v1/events",
        json={
            "user_id": user_id,
            "session_id": f"s_{user_id}",
            "event_type": "click",
            "event_time": datetime.now(timezone.utc).isoformat(),
            "attributes": {"label": label},
        },
    )
    assert response.status_code == 201


def test_value_seeker_fixture_batch() -> None:
    for idx in range(25):
        user = f"u_value_{idx}"
        _ingest(user, "discount_banner")
        _ingest(user, "discount_carousel")
        decide_response = client.post(
            "/api/v1/personalization/decide",
            json={"user_id": user, "session_id": f"s_{user}", "page_type": "home", "context": {}},
        )
        assert decide_response.status_code == 200
        assert decide_response.json()["segment"]["segment_name"] == "value_seeker"


def test_new_visitor_fixture_batch() -> None:
    for idx in range(25):
        user = f"u_new_{idx}"
        decide_response = client.post(
            "/api/v1/personalization/decide",
            json={"user_id": user, "session_id": f"s_{user}", "page_type": "plp", "context": {}},
        )
        assert decide_response.status_code == 200
        assert decide_response.json()["segment"]["segment_name"] in {"new_visitor", "considering"}
