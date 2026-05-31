# Project 14 Requirements Contract (2-Week Freeze)

## 1) Problem Statement
Modern ecommerce teams collect user clicks and purchases, but most stores still serve generic pages, static pricing, and broad promotions. This causes lower engagement, lower conversion, and missed revenue because the experience does not match each shopper's intent in the moment. Project 14 solves this by combining behavior tracking, segmentation, recommendations, pricing decisions, and content personalization into one coordinated personalization pipeline. The goal of this 2-week MVP is to prove that coordinated personalization can be delivered safely, measurably, and with clear operational boundaries.

## 2) In-Scope Features (Will Be Built and Demoed)
1. Real-time behavior event ingestion API for click, search, add-to-cart, and purchase events.
2. Customer segmentation service that assigns each user to one active segment using rule-based logic.
3. Product recommendation service that returns top-N products based on segment + recent events.
4. Dynamic pricing suggestion service that outputs allowed discount/promo recommendations (not direct catalog writes).
5. Content personalization service that returns layout/content variant IDs for homepage and product list page.
6. Personalization orchestrator that combines all feature outputs into one unified response.
7. Supabase persistence for events, profiles, segments, and decision logs.
8. Demo UI panel showing live user profile, segment, recommendations, pricing suggestions, and selected content variant.
9. Observability basics: request IDs, latency logs, and decision trace payload stored per personalization call.

## 3) Out-of-Scope Features (Will NOT Be Built)
1. Production-grade ML training pipeline - reason: model training and MLOps exceed 2-week MVP capacity.
2. Multi-armed bandit or reinforcement learning optimization - reason: requires longer experiment horizon and risk controls.
3. Direct checkout price mutation in production catalog - reason: pricing governance and legal approvals are out of MVP scope.
4. Full CMS/WYSIWYG page builder - reason: high frontend complexity not required to validate personalization logic.
5. Native mobile apps - reason: web MVP is sufficient for proving business value.
6. Enterprise auth/SSO hardening - reason: not required for controlled demo users.
7. Multi-region deployment and auto-scaling - reason: infra optimization is not needed for MVP validation.

## 4) Assumptions
- Environment assumptions:
  - Local/dev environment uses Python 3.11+, FastAPI backend, React + TypeScript frontend, Supabase hosted project.
  - One shared staging environment is available for final demo.
- Data assumptions:
  - Seed catalog and synthetic user-event data are available.
  - Product inventory and baseline price data are refreshed at least daily.
- User assumptions:
  - Demo supports authenticated internal test users only.
  - Each session is mapped to a known user ID.
- Integration assumptions:
  - Supabase credentials and tables can be provisioned before Day 2.
  - No dependency on external ecommerce platform write APIs for MVP.
- LLM assumptions:
  - LLM use is optional and limited to explanation text (why recommendation/pricing/content was selected).
  - Core decisions remain deterministic/rule-based for reliability in 2 weeks.

## 5) Success Criteria (Definition of COMPLETE)
1. End-to-end personalization API p95 latency is <= 500 ms on seeded test dataset for 100 sequential requests.
2. For a fixed test suite of 50 user scenarios, segmentation and recommendation outputs match expected fixtures in >= 90% of cases.
3. Every personalization response writes a decision trace record to Supabase with event context, chosen segment, and feature outputs.
4. Demo flow shows visibly different recommendations, promo suggestions, and layout variants across at least 3 segments.
5. Final demo checklist in DELIVERABLES.md is fully green with no blocker severity defects.

## 6) Deliverables List (Pointer)
The complete deliverables contract is defined in DELIVERABLES.md. This requirements file only freezes the scope baseline.

## 7) 2-Week Capacity Reality Check
- Team capacity assumption: 1-2 engineers + Copilot-assisted execution.
- Estimated effort envelope: ~70-90 focused engineering hours.
- What makes this feasible:
  - Rule-based segmentation/pricing (no model training loop).
  - One orchestrated response contract instead of multiple complex UIs.
  - Limited UI surface: operator/demo panel only.
  - Supabase as managed persistence (avoid custom infra buildout).
- Risk controls:
  - Freeze this file before implementation starts.
  - Any scope change requires re-baselining PLAN.md, CHECKPOINTS.md, and DELIVERABLES.md.
  - Stretch items are tracked only in FUTURE_VISION.md and never committed into current sprint scope.

## Scope Freeze Rule
This file is the source-of-truth contract for Project 14. If REQUIREMENTS.md changes, all downstream planning and execution docs must be fully revised before further implementation.