from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4


class EventType(str, Enum):
    click = "click"
    search = "search"
    add_to_cart = "add_to_cart"
    purchase = "purchase"


@dataclass(slots=True)
class BehaviorEvent:
    user_id: str
    session_id: str
    event_type: EventType
    event_time: datetime
    attributes: dict[str, Any]
    id: str = field(default_factory=lambda: str(uuid4()))
    request_id: str = field(default_factory=lambda: str(uuid4()))


@dataclass(slots=True)
class SegmentDecision:
    segment_id: str
    segment_name: str
    confidence: float
    reason_codes: list[str]


@dataclass(slots=True)
class Product:
    product_id: str
    title: str
    category: str
    base_price: float
    inventory_count: int


@dataclass(slots=True)
class RecommendationItem:
    product_id: str
    score: float
    reason: str


@dataclass(slots=True)
class PricingSuggestion:
    product_id: str
    promo_type: str
    discount_pct: int
    reason: str


@dataclass(slots=True)
class ContentDecision:
    variant_id: str
    slot_map: dict[str, str]
    reason: str


@dataclass(slots=True)
class DecisionTrace:
    trace_id: str
    user_id: str
    page_type: str
    segment_payload: dict[str, Any]
    rec_payload: list[dict[str, Any]]
    pricing_payload: list[dict[str, Any]]
    content_payload: dict[str, Any]
    latency_ms: int
    error_notes: list[str]
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
