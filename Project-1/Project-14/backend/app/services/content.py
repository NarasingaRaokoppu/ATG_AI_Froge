from __future__ import annotations

from app.models.domain import ContentDecision, SegmentDecision


class ContentPersonalizationService:
    def select(self, segment: SegmentDecision, page_type: str) -> ContentDecision:
        if page_type not in {"home", "plp"}:
            return ContentDecision("default_variant", {"hero": "default"}, "unknown_page_type")

        if segment.segment_name == "value_seeker":
            hero = "discount"
            rail = "trending_deals"
            variant_id = f"{page_type}_discount_banner_a"
        elif segment.segment_name == "loyal_buyer":
            hero = "premium"
            rail = "member_exclusives"
            variant_id = f"{page_type}_premium_showcase_b"
        elif segment.segment_name == "considering":
            hero = "social_proof"
            rail = "best_sellers"
            variant_id = f"{page_type}_confidence_builder_c"
        else:
            hero = "discover"
            rail = "new_arrivals"
            variant_id = f"{page_type}_onboarding_d"

        return ContentDecision(
            variant_id=variant_id,
            slot_map={"hero": hero, "rail_1": rail},
            reason=f"segment_layout_policy:{segment.segment_name}",
        )
