from __future__ import annotations

from app.repositories.base import PersonalizationRepository
from app.schemas.personalization import TraceResponse, UserProfileResponse


class ProfileService:
    def __init__(self, repo: PersonalizationRepository) -> None:
        self.repo = repo

    def get_user_profile(self, user_id: str) -> UserProfileResponse:
        segment = self.repo.get_active_segment(user_id)
        recent_events = self.repo.get_recent_events(user_id, limit=100)
        trace = self.repo.get_last_trace_for_user(user_id)

        return UserProfileResponse(
            user_id=user_id,
            active_segment=segment.segment_id if segment else "seg_new_visitor",
            recent_events=len(recent_events),
            last_trace_id=trace.trace_id if trace else None,
        )

    def get_trace(self, trace_id: str) -> TraceResponse:
        trace = self.repo.get_trace(trace_id)
        if not trace:
            return TraceResponse(trace_id=trace_id, status="not_found", decision={})

        return TraceResponse(
            trace_id=trace_id,
            status="ok",
            decision={
                "user_id": trace.user_id,
                "page_type": trace.page_type,
                "segment": trace.segment_payload,
                "recommendations": trace.rec_payload,
                "pricing": trace.pricing_payload,
                "content": trace.content_payload,
                "latency_ms": trace.latency_ms,
                "error_notes": trace.error_notes,
            },
        )
