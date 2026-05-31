# Copilot Instructions for Project 14

## Mission
Build only the frozen MVP scope for a hyper-personalized shopping experience as defined in REQUIREMENTS.md.

## Golden Rule
If a requested change is outside REQUIREMENTS.md in-scope items, do not implement it. Record it in FUTURE_VISION.md instead.

## Tech Stack
- Backend: FastAPI, Python 3.11+
- Frontend: React + TypeScript
- Data: Supabase (Postgres)
- Testing: Pytest for backend, basic UI checks for demo panel

## Folder Structure (Project 14)
- backend/
  - app/models/
  - app/schemas/
  - app/services/
  - app/agents/
  - app/graphs/
  - app/api/
- frontend/
  - src/pages/
  - src/components/
  - src/services/
- docs/

## Build Order Rule
Implement in this order only:
1. models
2. schemas
3. services
4. agents
5. graphs
6. routes
7. UI

## Agent Rules
1. Behavior Tracking Agent: normalization + write only.
2. Segmentation Agent: deterministic rule logic only.
3. Recommendation Agent: top-N ranked output only.
4. Pricing Agent: suggestions only, no direct catalog mutation.
5. Content Agent: variant selection only.
6. Orchestrator Agent: merge all outputs + persist trace.

## Implementation Guardrails
1. Keep business logic in services, not routes.
2. Every API output includes trace_id where applicable.
3. Structured error responses only.
4. Add tests for normal path and edge cases.
5. No silent fallback that hides errors.

## Documentation Guardrails
1. Update CHECKPOINTS.md status during execution.
2. Keep DELIVERABLES.md as source of demo readiness.
3. Do not change REQUIREMENTS.md after coding starts unless full re-baseline is performed.

## Prohibited Actions
1. Adding out-of-scope features into current phase.
2. Replacing deterministic core logic with unbounded LLM decisions.
3. Skipping gate checks to accelerate timeline.