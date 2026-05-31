# PLAN.md (2-Week Execution)

## Scope Mapping Rule
Only tasks that map to REQUIREMENTS.md in-scope items are allowed in this plan.

## Week 1

### Milestone 1 (Days 1-2): Contract and Data Foundation
- Lock REQUIREMENTS.md freeze and align all docs.
- Define schemas and API contracts in SPEC.md.
- Create Supabase tables and seed scripts for users/products/events.
- Deliverables mapped:
  - In-scope 1, 7.

### Milestone 2 (Days 3-4): Core Services
- Implement event ingestion service and validation.
- Implement segmentation service (rule-based).
- Implement recommendation service baseline.
- Deliverables mapped:
  - In-scope 1, 2, 3.

### Milestone 3 (Day 5): Decision Services
- Implement dynamic pricing suggestion service with guardrails.
- Implement content personalization variant selection.
- Add unit tests for deterministic outputs.
- Deliverables mapped:
  - In-scope 4, 5.

## Week 2

### Milestone 4 (Days 6-7): Orchestration and Persistence
- Build orchestrator decision flow and partial-failure fallbacks.
- Persist decision traces and metrics to Supabase.
- Expose trace retrieval endpoint.
- Deliverables mapped:
  - In-scope 6, 7, 9.

### Milestone 5 (Days 8-9): Demo UI and Integration
- Build demo/operator panel for live personalization outcomes.
- Integrate APIs for user profile + decision visualization.
- Add latency and status indicators.
- Deliverables mapped:
  - In-scope 8, 9.

### Milestone 6 (Days 10-11): Validation and Hardening
- Run fixture-based validation for 50 scenarios.
- Run latency measurement sequence (100 requests).
- Fix blocker defects and finalize checkpoint evidence.
- Deliverables mapped:
  - Success criteria 1-5.

### Milestone 7 (Days 12-14): Demo Readiness
- Execute full final demo checklist.
- Finalize docs, architecture diagram, and phase status.
- Prepare contingency script for fallback demo.
- Deliverables mapped:
  - DELIVERABLES.md full green.

## Resourcing and Capacity
- Primary assumption: 1-2 engineers.
- Copilot used for scaffold/test generation and refactor loops.
- No stretch items included in baseline timeline.

## Change Control
Any change to REQUIREMENTS.md invalidates this plan until updated and re-approved.