from __future__ import annotations

from app.models.domain import BehaviorEvent, DecisionTrace, Product, SegmentDecision
from app.repositories.base import PersonalizationRepository


class InMemoryPersonalizationRepository(PersonalizationRepository):
    def __init__(self) -> None:
        self.events: list[BehaviorEvent] = []
        self.segments: dict[str, SegmentDecision] = {}
        self.traces: dict[str, DecisionTrace] = {}
        self.products: list[Product] = [
            Product("p_1001", "Smart Running Shoes", "sports", 89.0, 48),
            Product("p_1002", "Premium Leather Bag", "fashion", 220.0, 15),
            Product("p_1003", "Noise Canceling Headphones", "electronics", 179.0, 32),
            Product("p_1004", "Daily Essentials Bundle", "grocery", 39.0, 64),
            Product("p_1005", "Designer Sunglasses", "fashion", 140.0, 19),
            Product("p_1006", "Wireless Charger", "electronics", 35.0, 70),
        ]

    def save_event(self, event: BehaviorEvent) -> None:
        self.events.append(event)

    def get_recent_events(self, user_id: str, limit: int = 50) -> list[BehaviorEvent]:
        filtered = [event for event in self.events if event.user_id == user_id]
        return filtered[-limit:]

    def save_segment(self, user_id: str, segment: SegmentDecision) -> None:
        self.segments[user_id] = segment

    def get_active_segment(self, user_id: str) -> SegmentDecision | None:
        return self.segments.get(user_id)

    def list_products(self) -> list[Product]:
        return self.products

    def save_trace(self, trace: DecisionTrace) -> None:
        self.traces[trace.trace_id] = trace

    def get_trace(self, trace_id: str) -> DecisionTrace | None:
        return self.traces.get(trace_id)

    def get_last_trace_for_user(self, user_id: str) -> DecisionTrace | None:
        user_traces = [trace for trace in self.traces.values() if trace.user_id == user_id]
        if not user_traces:
            return None
        return sorted(user_traces, key=lambda trace: trace.created_at)[-1]
