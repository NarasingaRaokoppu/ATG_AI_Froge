from __future__ import annotations

import psycopg2
from psycopg2.extras import Json

from app.models.domain import BehaviorEvent, DecisionTrace, EventType, Product, SegmentDecision
from app.repositories.base import PersonalizationRepository


class PostgresPersonalizationRepository(PersonalizationRepository):
    def __init__(self, database_url: str) -> None:
        self.database_url = database_url

    def _connect(self):
        dsn = self.database_url.replace("postgresql+asyncpg://", "postgresql://")
        return psycopg2.connect(dsn)

    def save_event(self, event: BehaviorEvent) -> None:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                insert into behavior_events (id, user_id, session_id, event_type, event_time, attributes, request_id)
                values (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    event.id,
                    event.user_id,
                    event.session_id,
                    event.event_type.value,
                    event.event_time,
                    Json(event.attributes),
                    event.request_id,
                ),
            )

    def get_recent_events(self, user_id: str, limit: int = 50) -> list[BehaviorEvent]:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                select id, user_id, session_id, event_type, event_time, attributes, request_id
                from behavior_events
                where user_id = %s
                order by event_time asc
                limit %s
                """,
                (user_id, limit),
            )
            rows = cur.fetchall()

        events: list[BehaviorEvent] = []
        for row in rows:
            events.append(
                BehaviorEvent(
                    id=str(row[0]),
                    user_id=row[1],
                    session_id=row[2],
                    event_type=EventType(row[3]),
                    event_time=row[4],
                    attributes=row[5] or {},
                    request_id=row[6],
                )
            )
        return events

    def save_segment(self, user_id: str, segment: SegmentDecision) -> None:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                insert into user_segments (user_id, segment_id, segment_name, confidence, reason_codes, updated_at)
                values (%s, %s, %s, %s, %s, now())
                on conflict (user_id)
                do update set
                  segment_id = excluded.segment_id,
                  segment_name = excluded.segment_name,
                  confidence = excluded.confidence,
                  reason_codes = excluded.reason_codes,
                  updated_at = now()
                """,
                (
                    user_id,
                    segment.segment_id,
                    segment.segment_name,
                    segment.confidence,
                    Json(segment.reason_codes),
                ),
            )

    def get_active_segment(self, user_id: str) -> SegmentDecision | None:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                select segment_id, segment_name, confidence, reason_codes
                from user_segments
                where user_id = %s
                limit 1
                """,
                (user_id,),
            )
            row = cur.fetchone()

        if not row:
            return None

        return SegmentDecision(
            segment_id=row[0],
            segment_name=row[1],
            confidence=float(row[2]),
            reason_codes=row[3] or [],
        )

    def list_products(self) -> list[Product]:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                select id, title, category, base_price, inventory_count
                from products
                order by id asc
                """
            )
            rows = cur.fetchall()

        return [
            Product(
                product_id=row[0],
                title=row[1],
                category=row[2],
                base_price=float(row[3]),
                inventory_count=int(row[4]),
            )
            for row in rows
        ]

    def save_trace(self, trace: DecisionTrace) -> None:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                insert into personalization_decisions (
                  trace_id, user_id, page_type, segment_payload, rec_payload,
                  pricing_payload, content_payload, latency_ms, error_notes, created_at
                )
                values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    trace.trace_id,
                    trace.user_id,
                    trace.page_type,
                    Json(trace.segment_payload),
                    Json(trace.rec_payload),
                    Json(trace.pricing_payload),
                    Json(trace.content_payload),
                    trace.latency_ms,
                    Json(trace.error_notes),
                    trace.created_at,
                ),
            )

    def get_trace(self, trace_id: str) -> DecisionTrace | None:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                select trace_id, user_id, page_type, segment_payload, rec_payload,
                       pricing_payload, content_payload, latency_ms, error_notes, created_at
                from personalization_decisions
                where trace_id = %s
                limit 1
                """,
                (trace_id,),
            )
            row = cur.fetchone()

        if not row:
            return None

        return DecisionTrace(
            trace_id=row[0],
            user_id=row[1],
            page_type=row[2],
            segment_payload=row[3] or {},
            rec_payload=row[4] or [],
            pricing_payload=row[5] or [],
            content_payload=row[6] or {},
            latency_ms=int(row[7]),
            error_notes=row[8] or [],
            created_at=row[9],
        )

    def get_last_trace_for_user(self, user_id: str) -> DecisionTrace | None:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                select trace_id, user_id, page_type, segment_payload, rec_payload,
                       pricing_payload, content_payload, latency_ms, error_notes, created_at
                from personalization_decisions
                where user_id = %s
                order by created_at desc
                limit 1
                """,
                (user_id,),
            )
            row = cur.fetchone()

        if not row:
            return None

        return DecisionTrace(
            trace_id=row[0],
            user_id=row[1],
            page_type=row[2],
            segment_payload=row[3] or {},
            rec_payload=row[4] or [],
            pricing_payload=row[5] or [],
            content_payload=row[6] or {},
            latency_ms=int(row[7]),
            error_notes=row[8] or [],
            created_at=row[9],
        )
