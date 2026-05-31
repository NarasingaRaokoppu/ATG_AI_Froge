from __future__ import annotations

from app.core.config import settings
from app.models.domain import PricingSuggestion, SegmentDecision
from app.repositories.base import PersonalizationRepository


class PricingService:
    def __init__(self, repo: PersonalizationRepository) -> None:
        self.repo = repo

    def suggest(self, segment: SegmentDecision, product_ids: list[str]) -> list[PricingSuggestion]:
        products = {product.product_id: product for product in self.repo.list_products()}
        suggestions: list[PricingSuggestion] = []

        for product_id in product_ids:
            product = products.get(product_id)
            if not product:
                continue

            if segment.segment_name == "value_seeker":
                discount = 12 if product.inventory_count > 20 else 8
            elif segment.segment_name == "loyal_buyer":
                discount = 5
            elif segment.segment_name == "considering":
                discount = 7
            else:
                discount = 4

            safe_discount = max(0, min(settings.max_discount_pct, discount))
            suggestions.append(
                PricingSuggestion(
                    product_id=product.product_id,
                    promo_type="percentage",
                    discount_pct=safe_discount,
                    reason=f"segment_pricing_policy:{segment.segment_name}",
                )
            )

        return suggestions
