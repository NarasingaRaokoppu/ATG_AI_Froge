from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class EventIngestRequest(BaseModel):
    user_id: str = Field(min_length=1)
    session_id: str = Field(min_length=1)
    event_type: Literal["click", "search", "add_to_cart", "purchase"]
    event_time: datetime
    attributes: dict[str, Any] = Field(default_factory=dict)


class EventIngestResponse(BaseModel):
    event_id: str
    status: str = "accepted"


class OrchestratorRequest(BaseModel):
    user_id: str = Field(min_length=1)
    session_id: str = Field(min_length=1)
    page_type: Literal["home", "plp"]
    context: dict[str, Any] = Field(default_factory=dict)


class SegmentPayload(BaseModel):
    segment_id: str
    segment_name: str
    confidence: float
    reasons: list[str]


class RecommendationPayload(BaseModel):
    product_id: str
    score: float
    reason: str


class PricingPayload(BaseModel):
    product_id: str
    promo_type: str
    discount_pct: int
    reason: str


class ContentPayload(BaseModel):
    variant_id: str
    slot_map: dict[str, str]
    reason: str


class MetaPayload(BaseModel):
    latency_ms: int
    fallback_used: bool


class OrchestratorResponse(BaseModel):
    trace_id: str
    user_id: str
    segment: SegmentPayload
    recommendations: list[RecommendationPayload]
    pricing: list[PricingPayload]
    content: ContentPayload
    meta: MetaPayload


class UserProfileResponse(BaseModel):
    user_id: str
    active_segment: str
    recent_events: int
    last_trace_id: str | None


class TraceResponse(BaseModel):
    trace_id: str
    status: str
    decision: dict[str, Any]
