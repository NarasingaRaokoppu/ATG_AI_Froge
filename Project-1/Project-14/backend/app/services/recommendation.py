from __future__ import annotations

from app.models.domain import RecommendationItem, SegmentDecision
from app.repositories.base import PersonalizationRepository


class RecommendationService:
    def __init__(self, repo: PersonalizationRepository) -> None:
        self.repo = repo

    def top_n(self, segment: SegmentDecision, n: int = 6) -> list[RecommendationItem]:
        products = [product for product in self.repo.list_products() if product.inventory_count > 0]

        ranked: list[RecommendationItem] = []
        for product in products:
            base_score = min(0.99, (product.inventory_count / 100) + 0.2)
            if segment.segment_name == "value_seeker":
                base_score += 0.1 if product.base_price < 100 else -0.05
            elif segment.segment_name == "loyal_buyer":
                base_score += 0.08 if product.base_price >= 100 else 0.02
            elif segment.segment_name == "considering":
                base_score += 0.06 if product.category in {"electronics", "fashion"} else 0.01

            ranked.append(
                RecommendationItem(
                    product_id=product.product_id,
                    score=round(min(0.99, base_score), 2),
                    reason=f"segment_match:{segment.segment_name}",
                )
            )

        return sorted(ranked, key=lambda item: item.score, reverse=True)[: min(n, 12)]
