# Project 14 - Hyper-Personalized Shopping MVP

## What This Project Does
Project 14 delivers a 2-week MVP that personalizes ecommerce experiences using coordinated feature services: behavior tracking, customer segmentation, product recommendation, dynamic pricing suggestions, and content personalization. Outputs are merged by an orchestrator into one unified decision payload and persisted to Supabase for traceability.

## Why This Exists
The project demonstrates how to move from generic storefront behavior to segment-aware, adaptive user journeys without overcommitting to long-cycle ML infrastructure in an MVP timeframe.

## Current Phase Status
- Phase 0: Scope Freeze - complete
- Phase 1: Data and Contracts - complete
- Phase 2: Core Feature Services - complete
- Phase 3: Orchestration and Persistence - complete (in-memory validated, Supabase adapter included)
- Phase 4: UI and Demo Integration - complete
- Phase 5: Final Acceptance - complete for local end-to-end run

## Entry Documents
1. REQUIREMENTS.md - frozen scope and completion criteria.
2. FUTURE_VISION.md - deferred and stretch direction.
3. MVP_PREVIEW.md - expected 2-week outcome.
4. AI_FIRST_STRATEGY.md - spec-driven + prompt-driven execution strategy.
5. SPEC.md - agent behavior, schemas, data model, and API contracts.
6. PLAN.md - 2-week milestones.
7. DEPENDENCIES.md - strict build order.
8. PROMPT_SEQUENCES.md - Copilot prompt patterns.
9. CHECKPOINTS.md - gate-based progression rules.
10. DELIVERABLES.md - final demo checklist.
11. docs/architecture.mmd - canonical architecture flow.
12. WORKSTREAMS.md - senior backend, frontend, and UI ownership model.

## How to Run
1. Backend API
   - cd Project-14/backend
   - pip install -r requirements.txt
   - uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
2. Backend tests
   - cd Project-14/backend
   - pytest -q
3. Frontend UI
   - cd Project-14/frontend
   - npm install
   - npm run dev
4. Frontend production build
   - cd Project-14/frontend
   - npm run build
5. Latency benchmark (100 requests)
   - cd Project-14/backend
   - python scripts/benchmark_latency.py
6. Supabase setup (optional runtime mode)
   - Run backend/sql/schema.sql and backend/sql/seed_products.sql in Supabase SQL editor
   - Set USE_IN_MEMORY_REPO=false and provide SUPABASE_URL, SUPABASE_KEY in backend/.env

## Verified Results
1. Backend test suite: 5 passed.
2. Frontend production build: success.
3. Latency benchmark (100 sequential requests): p95 8.34 ms.

## Architecture at Runtime
1. POST /api/v1/events ingests behavior events.
2. POST /api/v1/personalization/decide orchestrates segmentation, recommendations, pricing, and content.
3. GET /api/v1/users/{user_id}/profile returns active profile summary.
4. GET /api/v1/traces/{trace_id} returns full decision trace.

## Scope Control
Do not implement features outside REQUIREMENTS.md. Any scope change requires re-baselining PLAN.md, CHECKPOINTS.md, and DELIVERABLES.md before coding continues.