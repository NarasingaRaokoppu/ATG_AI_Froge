from __future__ import annotations

import time
from dataclasses import asdict
from uuid import uuid4

from app.models.domain import DecisionTrace
from app.repositories.base import PersonalizationRepository
from app.schemas.personalization import OrchestratorRequest, OrchestratorResponse
from app.services.content import ContentPersonalizationService
from app.services.pricing import PricingService
from app.services.recommendation import RecommendationService
from app.services.segmentation import SegmentationService


class OrchestratorService:
    def __init__(
        self,
        repo: PersonalizationRepository,
        segmentation_service: SegmentationService,
        recommendation_service: RecommendationService,
        pricing_service: PricingService,
        content_service: ContentPersonalizationService,
    ) -> None:
        self.repo = repo
        self.segmentation_service = segmentation_service
        self.recommendation_service = recommendation_service
        self.pricing_service = pricing_service
        self.content_service = content_service

    def decide(self, payload: OrchestratorRequest) -> OrchestratorResponse:
        start = time.perf_counter()
        trace_id = f"trc_{uuid4()}"
        errors: list[str] = []
        fallback_used = False

        segment = self.segmentation_service.evaluate(payload.user_id)

        try:
            recommendations = self.recommendation_service.top_n(segment, n=6)
        except Exception as exc:  # pragma: no cover
            errors.append(f"recommendation_failed:{exc}")
            fallback_used = True
            recommendations = []

        try:
            pricing = self.pricing_service.suggest(segment, [item.product_id for item in recommendations])
        except Exception as exc:  # pragma: no cover
            errors.append(f"pricing_failed:{exc}")
            fallback_used = True
            pricing = []

        try:
            content = self.content_service.select(segment, payload.page_type)
        except Exception as exc:  # pragma: no cover
            errors.append(f"content_failed:{exc}")
            fallback_used = True
            content = self.content_service.select(segment, "home")

        latency_ms = int((time.perf_counter() - start) * 1000)

        response = OrchestratorResponse(
            trace_id=trace_id,
            user_id=payload.user_id,
            segment={
                "segment_id": segment.segment_id,
                "segment_name": segment.segment_name,
                "confidence": segment.confidence,
                "reasons": segment.reason_codes,
            },
            recommendations=[asdict(item) for item in recommendations],
            pricing=[asdict(item) for item in pricing],
            content=asdict(content),
            meta={"latency_ms": latency_ms, "fallback_used": fallback_used},
        )

        trace = DecisionTrace(
            trace_id=trace_id,
            user_id=payload.user_id,
            page_type=payload.page_type,
            segment_payload=response.segment.model_dump(),
            rec_payload=[item.model_dump() for item in response.recommendations],
            pricing_payload=[item.model_dump() for item in response.pricing],
            content_payload=response.content.model_dump(),
            latency_ms=latency_ms,
            error_notes=errors,
        )
        self.repo.save_trace(trace)

        return response
