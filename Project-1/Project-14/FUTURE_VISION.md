# Project 14 Future Vision

## In-Scope MVP (2 Weeks)
1. Event ingestion, segmentation, recommendations, pricing suggestions, and content variant selection.
2. Unified personalization orchestrator API.
3. Supabase-backed decision trace and profile history.
4. Demo UI that proves personalized outputs differ by user segment.

## Out-of-Scope for MVP (Deferred)
1. Continuous model training and feature store.
2. Real-time experimentation engine (A/B and multi-armed bandits).
3. Production catalog and checkout integration with hard guarantees.
4. Cross-device identity stitching and attribution.
5. Enterprise governance (RBAC matrix, audit dashboards, legal policy engine).

## Stretch Goals (Only if Core Scope Is Green)
1. Experiment flag support for recommendation strategy switching.
2. Lightweight uplift analytics dashboard (CTR/ATC proxy metrics on test data).
3. Explainability overlay in UI showing top decision factors.
4. Session-level anomaly detector for personalization conflicts.
5. Retry/dead-letter handling for failed event writes.

## Long-Term Direction (Post-MVP)
1. Move from rules to hybrid ML + rules architecture.
2. Introduce online/offline evaluation pipeline with guardrails.
3. Add channel personalization beyond web (email, push, onsite banners).
4. Add policy-aware dynamic pricing with legal and business constraints.
5. Build experimentation-first architecture where every decision can be tested safely.