# CHECKPOINTS.md

## Gate Policy
You cannot start the next phase until all current gate criteria are green.

## Phase 0 Gate: Scope Freeze
Criteria:
1. REQUIREMENTS.md finalized and reviewed.
2. SPEC.md, PLAN.md, and DELIVERABLES.md are aligned to frozen scope.
3. Out-of-scope list is explicit and acknowledged.
Evidence:
- Document review sign-off note.

## Phase 1 Gate: Data and Contracts
Criteria:
1. Supabase tables created and seed data loaded.
2. Event and orchestrator schemas validated.
3. API contracts documented and example payloads verified.
Evidence:
- Migration logs.
- Schema validation tests green.

## Phase 2 Gate: Core Feature Services
Criteria:
1. Behavior tracking service accepts valid events and rejects invalid events.
2. Segmentation service deterministic across fixed fixtures.
3. Recommendation service returns valid top-N output.
4. Pricing and content services enforce MVP guardrails.
Evidence:
- Unit tests for each service.
- Fixture comparison report.

## Phase 3 Gate: Orchestration and Persistence
Criteria:
1. Orchestrator returns unified response with trace_id.
2. Partial failure behavior returns valid fallback outputs.
3. Decision traces are written to Supabase for every request.
Evidence:
- Integration tests green.
- Supabase trace query screenshots/logs.

## Phase 4 Gate: UI and Demo Integration
Criteria:
1. Demo panel renders live segment, recommendations, pricing, content variant.
2. UI handles loading/error states without crash.
3. Trace lookup is visible for operator verification.
Evidence:
- UI test pass.
- Demo recording snippet.

## Phase 5 Gate: Final Acceptance
Criteria:
1. All success criteria in REQUIREMENTS.md are met.
2. All items in DELIVERABLES.md are complete.
3. No blocker severity defects remain open.
Evidence:
- Final checklist snapshot.
- Test summary and latency report.

## Gate Failure Protocol
1. Stop next-phase development immediately.
2. Log failed criteria and root cause.
3. Apply minimal fixes.
4. Re-run gate checks until green.