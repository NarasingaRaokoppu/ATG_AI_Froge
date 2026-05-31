# MVP Preview (What You Will See After 2 Weeks)

## Demo Narrative
A demo user lands on the storefront and starts interacting (search, clicks, add-to-cart, purchase). The system ingests each event and continuously updates user context. On each personalization call, five feature services run and the orchestrator returns one unified personalization payload. The UI updates recommended products, promo suggestions, and content variant in near real time.

## User-Visible Experience
1. User A (value seeker) receives discount-forward products and promotional messaging.
2. User B (premium segment) receives premium catalog ranking with low-discount positioning.
3. User C (new visitor) receives discovery-oriented recommendations and onboarding layout variant.

## Operator-Visible Experience
1. Live panel shows current segment, recent events, recommendation list, promo suggestion, and chosen content variant.
2. Decision trace panel shows why each output was selected and confirms write success to Supabase.
3. Health indicators show request latency, processing status, and fallback states.

## Technical Snapshot
- Backend: FastAPI services with orchestrator endpoint.
- Data: Supabase tables for events, profiles, segments, and decisions.
- Frontend: React TypeScript demo surface for personalization outcomes.
- Decision method: deterministic rule-based logic with optional LLM-generated explanation text.

## Non-Goals in MVP Preview
- No autonomous model retraining.
- No production checkout price write.
- No enterprise scalability claims.

## Acceptance Preview
The MVP is accepted when all items in DELIVERABLES.md are demonstrably green and success criteria in REQUIREMENTS.md are met.