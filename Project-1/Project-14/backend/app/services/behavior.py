from __future__ import annotations

from app.models.domain import BehaviorEvent, EventType
from app.repositories.base import PersonalizationRepository
from app.schemas.personalization import EventIngestRequest


class BehaviorTrackingService:
    def __init__(self, repo: PersonalizationRepository) -> None:
        self.repo = repo

    def ingest(self, payload: EventIngestRequest) -> BehaviorEvent:
        event = BehaviorEvent(
            user_id=payload.user_id,
            session_id=payload.session_id,
            event_type=EventType(payload.event_type),
            event_time=payload.event_time,
            attributes=payload.attributes,
        )
        self.repo.save_event(event)
        return event
