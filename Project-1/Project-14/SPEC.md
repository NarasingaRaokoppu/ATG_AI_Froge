# SPEC.md

## 1) System Overview
Project 14 provides a unified personalization decision engine for ecommerce. It ingests behavior events, updates user context, computes segment-aware recommendations and pricing suggestions, selects content variants, and returns a single orchestration response.

## 2) Agent Specs

### 2.1 Behavior Tracking Agent
- Purpose: Normalize and persist user interaction events.
- Inputs:
  - user_id, session_id, event_type, event_time, attributes JSON.
- Outputs:
  - event_id, normalized event payload, write status.
- Rules:
  - Reject unknown event_type.
  - Attach request_id for traceability.

### 2.2 Customer Segmentation Agent
- Purpose: Assign one active segment from event + profile context.
- Inputs:
  - user profile, rolling event summary, optional demographics.
- Outputs:
  - segment_id, segment_name, confidence, reason_codes.
- Rules:
  - Rule-based scoring for MVP.
  - Deterministic fallback segment: new_visitor.

### 2.3 Product Recommendation Agent
- Purpose: Return top-N products tailored to segment and recent behavior.
- Inputs:
  - segment_id, recent events, catalog snapshot.
- Outputs:
  - ranked products [{product_id, score, reason}].
- Rules:
  - Exclude out-of-stock items.
  - Default N=6, max N=12.

### 2.4 Dynamic Pricing Agent
- Purpose: Suggest promo/discount policy within guardrails.
- Inputs:
  - segment_id, product candidates, demand index, inventory level.
- Outputs:
  - pricing suggestions [{product_id, promo_type, discount_pct, reason}].
- Rules:
  - discount_pct must be between 0 and 20 for MVP.
  - Never write directly to source catalog in MVP.

### 2.5 Content Personalization Agent
- Purpose: Select content/layout variants for web surfaces.
- Inputs:
  - segment_id, page_type, context signals.
- Outputs:
  - variant_id, variant_slot_map, reason.
- Rules:
  - Allowed page_type: home, plp.
  - Unknown page_type returns default variant.

### 2.6 Orchestrator Agent
- Purpose: Combine outputs from all agents into one decision.
- Inputs:
  - user context + page context.
- Outputs:
  - personalization decision payload + trace_id.
- Rules:
  - On partial failure, include fallback decisions and error_notes.
  - Persist full trace to Supabase.

## 3) I/O Schemas (JSON)

### 3.1 Event Ingest Request
```json
{
  "user_id": "u_123",
  "session_id": "s_123",
  "event_type": "click",
  "event_time": "2026-05-31T12:00:00Z",
  "attributes": {
    "product_id": "p_1001",
    "page": "home"
  }
}
```

### 3.2 Orchestrator Request
```json
{
  "user_id": "u_123",
  "session_id": "s_123",
  "page_type": "home",
  "context": {
    "device": "web",
    "locale": "en-US"
  }
}
```

### 3.3 Orchestrator Response
```json
{
  "trace_id": "trc_001",
  "user_id": "u_123",
  "segment": {
    "segment_id": "seg_value_seeker",
    "confidence": 0.82,
    "reasons": ["high_discount_click_rate", "price_sort_usage"]
  },
  "recommendations": [
    {"product_id": "p_1001", "score": 0.91, "reason": "segment_match"}
  ],
  "pricing": [
    {"product_id": "p_1001", "promo_type": "percentage", "discount_pct": 10, "reason": "inventory_high"}
  ],
  "content": {
    "variant_id": "home_discount_banner_a",
    "slot_map": {"hero": "discount", "rail_1": "trending_deals"}
  },
  "meta": {
    "latency_ms": 238,
    "fallback_used": false
  }
}
```

## 4) Data Model (Supabase)

### 4.1 Tables
1. users
   - id (text, pk), created_at, attributes jsonb.
2. behavior_events
   - id (uuid, pk), user_id (fk), session_id, event_type, event_time, attributes jsonb, request_id.
3. user_segments
   - id (uuid, pk), user_id (fk), segment_id, confidence, reason_codes jsonb, updated_at.
4. products
   - id (text, pk), title, category, inventory_count, base_price, attributes jsonb.
5. personalization_decisions
   - id (uuid, pk), trace_id, user_id (fk), page_type, segment_payload jsonb, rec_payload jsonb, pricing_payload jsonb, content_payload jsonb, latency_ms, created_at.
6. system_metrics
   - id (uuid, pk), trace_id, status, error_notes jsonb, created_at.

## 5) API Contracts

### 5.1 POST /api/v1/events
- Description: ingest one normalized behavior event.
- Request: Event Ingest Request schema.
- Response 201:
```json
{"event_id": "uuid", "status": "accepted"}
```

### 5.2 POST /api/v1/personalization/decide
- Description: run full orchestration and return personalization output.
- Request: Orchestrator Request schema.
- Response 200: Orchestrator Response schema.

### 5.3 GET /api/v1/users/{user_id}/profile
- Description: get latest profile, segment, and summary stats.
- Response 200:
```json
{
  "user_id": "u_123",
  "active_segment": "seg_value_seeker",
  "recent_events": 20,
  "last_trace_id": "trc_001"
}
```

### 5.4 GET /api/v1/traces/{trace_id}
- Description: fetch decision trace for debugging/demo.
- Response 200:
```json
{
  "trace_id": "trc_001",
  "status": "ok",
  "decision": {}
}
```

## 6) Non-Functional Constraints
1. p95 decision latency <= 500 ms on seeded load.
2. Every response includes trace_id.
3. Deterministic decision behavior for same fixed inputs.
4. Input validation errors must return structured 4xx responses.

## 7) Traceability Rule
All implementation items in PLAN.md and DELIVERABLES.md must map to in-scope items frozen in REQUIREMENTS.md.