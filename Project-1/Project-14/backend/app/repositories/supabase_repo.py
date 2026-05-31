from __future__ import annotations

from datetime import datetime, timezone

from supabase import Client, create_client

from app.models.domain import BehaviorEvent, DecisionTrace, EventType, Product, SegmentDecision
from app.repositories.base import PersonalizationRepository


class SupabasePersonalizationRepository(PersonalizationRepository):
    def __init__(self, supabase_url: str, supabase_key: str) -> None:
        self.client: Client = create_client(supabase_url, supabase_key)

    def save_event(self, event: BehaviorEvent) -> None:
        self.client.table("behavior_events").insert(
            {
                "id": event.id,
                "user_id": event.user_id,
                "session_id": event.session_id,
                "event_type": event.event_type.value,
                "event_time": event.event_time.isoformat(),
                "attributes": event.attributes,
                "request_id": event.request_id,
            }
        ).execute()

    def get_recent_events(self, user_id: str, limit: int = 50) -> list[BehaviorEvent]:
        result = (
            self.client.table("behavior_events")
            .select("id,user_id,session_id,event_type,event_time,attributes,request_id")
            .eq("user_id", user_id)
            .order("event_time", desc=False)
            .limit(limit)
            .execute()
        )

        rows = result.data or []
        events: list[BehaviorEvent] = []
        for row in rows:
            event = BehaviorEvent(
                id=row["id"],
                user_id=row["user_id"],
                session_id=row["session_id"],
                event_type=EventType(row["event_type"]),
                event_time=datetime.fromisoformat(row["event_time"].replace("Z", "+00:00")),
                attributes=row.get("attributes") or {},
                request_id=row.get("request_id", ""),
            )
            events.append(event)
        return events

    def save_segment(self, user_id: str, segment: SegmentDecision) -> None:
        self.client.table("user_segments").upsert(
            {
                "user_id": user_id,
                "segment_id": segment.segment_id,
                "segment_name": segment.segment_name,
                "confidence": segment.confidence,
                "reason_codes": segment.reason_codes,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            },
            on_conflict="user_id",
        ).execute()

    def get_active_segment(self, user_id: str) -> SegmentDecision | None:
        result = (
            self.client.table("user_segments")
            .select("segment_id,segment_name,confidence,reason_codes")
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )
        rows = result.data or []
        if not rows:
            return None
        row = rows[0]
        return SegmentDecision(
            segment_id=row["segment_id"],
            segment_name=row["segment_name"],
            confidence=float(row["confidence"]),
            reason_codes=row.get("reason_codes") or [],
        )

    def list_products(self) -> list[Product]:
        result = self.client.table("products").select("id,title,category,base_price,inventory_count").execute()
        rows = result.data or []
        return [
            Product(
                product_id=row["id"],
                title=row["title"],
                category=row["category"],
                base_price=float(row["base_price"]),
                inventory_count=int(row["inventory_count"]),
            )
            for row in rows
        ]

    def save_trace(self, trace: DecisionTrace) -> None:
        self.client.table("personalization_decisions").insert(
            {
                "trace_id": trace.trace_id,
                "user_id": trace.user_id,
                "page_type": trace.page_type,
                "segment_payload": trace.segment_payload,
                "rec_payload": trace.rec_payload,
                "pricing_payload": trace.pricing_payload,
                "content_payload": trace.content_payload,
                "latency_ms": trace.latency_ms,
                "error_notes": trace.error_notes,
                "created_at": trace.created_at.isoformat(),
            }
        ).execute()

    def get_trace(self, trace_id: str) -> DecisionTrace | None:
        result = (
            self.client.table("personalization_decisions")
            .select(
                "trace_id,user_id,page_type,segment_payload,rec_payload,pricing_payload,content_payload,latency_ms,error_notes,created_at"
            )
            .eq("trace_id", trace_id)
            .limit(1)
            .execute()
        )
        rows = result.data or []
        if not rows:
            return None
        row = rows[0]
        return DecisionTrace(
            trace_id=row["trace_id"],
            user_id=row["user_id"],
            page_type=row["page_type"],
            segment_payload=row.get("segment_payload") or {},
            rec_payload=row.get("rec_payload") or [],
            pricing_payload=row.get("pricing_payload") or [],
            content_payload=row.get("content_payload") or {},
            latency_ms=int(row.get("latency_ms", 0)),
            error_notes=row.get("error_notes") or [],
            created_at=datetime.fromisoformat(row["created_at"].replace("Z", "+00:00")),
        )

    def get_last_trace_for_user(self, user_id: str) -> DecisionTrace | None:
        result = (
            self.client.table("personalization_decisions")
            .select(
                "trace_id,user_id,page_type,segment_payload,rec_payload,pricing_payload,content_payload,latency_ms,error_notes,created_at"
            )
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        rows = result.data or []
        if not rows:
            return None

        row = rows[0]
        return DecisionTrace(
            trace_id=row["trace_id"],
            user_id=row["user_id"],
            page_type=row["page_type"],
            segment_payload=row.get("segment_payload") or {},
            rec_payload=row.get("rec_payload") or [],
            pricing_payload=row.get("pricing_payload") or [],
            content_payload=row.get("content_payload") or {},
            latency_ms=int(row.get("latency_ms", 0)),
            error_notes=row.get("error_notes") or [],
            created_at=datetime.fromisoformat(row["created_at"].replace("Z", "+00:00")),
        )
