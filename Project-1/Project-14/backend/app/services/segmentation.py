from __future__ import annotations

from app.models.domain import EventType, SegmentDecision
from app.repositories.base import PersonalizationRepository


class SegmentationService:
    def __init__(self, repo: PersonalizationRepository) -> None:
        self.repo = repo

    def evaluate(self, user_id: str) -> SegmentDecision:
        events = self.repo.get_recent_events(user_id, limit=100)
        if not events:
            segment = SegmentDecision("seg_new_visitor", "new_visitor", 0.9, ["no_behavior_history"])
            self.repo.save_segment(user_id, segment)
            return segment

        purchase_count = sum(1 for event in events if event.event_type == EventType.purchase)
        add_to_cart_count = sum(1 for event in events if event.event_type == EventType.add_to_cart)
        discount_click_count = sum(1 for event in events if "discount" in str(event.attributes).lower())

        if purchase_count >= 3:
            segment = SegmentDecision(
                "seg_loyal_buyer", "loyal_buyer", 0.86, ["purchase_count>=3", "high_repeat_intent"]
            )
        elif discount_click_count >= 2:
            segment = SegmentDecision(
                "seg_value_seeker", "value_seeker", 0.82, ["discount_interaction", "price_sensitive_behavior"]
            )
        elif add_to_cart_count >= 2:
            segment = SegmentDecision(
                "seg_considering", "considering", 0.74, ["multiple_add_to_cart", "mid_funnel_behavior"]
            )
        else:
            segment = SegmentDecision("seg_new_visitor", "new_visitor", 0.68, ["low_signal_density"])

        self.repo.save_segment(user_id, segment)
        return segment
