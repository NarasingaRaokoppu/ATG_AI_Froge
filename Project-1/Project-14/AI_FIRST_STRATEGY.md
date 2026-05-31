# AI-First Development Strategy

## Strategy Choice
Hybrid specification-driven + prompt-driven development.

## Why This Strategy Fits a 2-Week MVP
1. Specification-driven design prevents scope drift and locks contracts early.
2. Prompt-driven execution accelerates implementation, test generation, and refactoring loops.
3. Combined approach keeps architecture stable while still moving quickly with AI assistance.

## Operating Principles
1. Contract before code: update SPEC.md first, then implement.
2. Prompt as executable plan: every major coding block starts from a structured Copilot prompt pattern.
3. Gate-driven progress: do not enter next phase until CHECKPOINTS.md gate is green.
4. Deterministic core decisions first, AI augmentation second.
5. Traceability required: each service output must be explainable and persisted.

## Development Loop
1. Define or refine requirement and API/schema contract.
2. Generate scaffold and tests using prompt sequences.
3. Implement minimal vertical slice.
4. Run gate checks and fix defects.
5. Merge only when gate is green and docs remain consistent.

## Prompt Discipline Rules
1. Use explicit input and output schema in every prompt.
2. Ask Copilot for test cases before finalizing implementation.
3. Keep prompts phase-bounded (models/schemas/services/agents/routes/UI).
4. Reject generated code that violates REQUIREMENTS.md freeze.
5. Prefer small, reviewable patches and visible checkpoints.

## Definition of Done for AI-First Execution
1. All generated artifacts map back to in-scope requirements.
2. Gate criteria pass without manual exception.
3. Final demo checklist is green.
4. Remaining gaps are documented as future scope only.