# PROMPT_SEQUENCES.md

## Purpose
Standard prompt patterns for Copilot Agent Mode to keep execution consistent, auditable, and aligned with frozen scope.

## Sequence 1: Contract-First Prompt
Use before any implementation.

```text
You are implementing Project 14. Read REQUIREMENTS.md and SPEC.md first.
Task: [feature/task name]
Scope guard: Only in-scope items are allowed.
Output needed:
1) Proposed changes list
2) Files to create/update
3) Tests to add
4) Risks and assumptions
Do not write code until schema and API contracts are confirmed.
```

## Sequence 2: Model and Schema Prompt
Use during data foundation phase.

```text
Implement data models and I/O schemas for [feature].
Constraints:
- Keep deterministic behavior.
- Include validation and default fallbacks.
- Return migration notes and schema examples.
Produce:
1) Model definitions
2) Request/response schemas
3) Minimal tests for schema validation
```

## Sequence 3: Service Implementation Prompt
Use for each core service.

```text
Implement service layer for [feature service].
Inputs: [schema refs]
Outputs: [schema refs]
Rules:
- Business logic in service only
- No framework-specific logic in core function
- Include error handling and fallback path
Also generate unit tests covering normal, edge, and invalid input cases.
```

## Sequence 4: Orchestrator Prompt
Use when connecting services.

```text
Build orchestrator flow using existing services:
1) segmentation
2) recommendations
3) pricing
4) content
Requirements:
- single trace_id
- partial-failure fallback behavior
- decision trace persistence
Return:
- orchestrator code
- integration tests
- sample response payload
```

## Sequence 5: API Route Prompt
Use after services are stable.

```text
Create FastAPI routes for [endpoint list] using frozen schemas.
Requirements:
- explicit response models
- structured error responses
- trace_id in all responses
Also provide API test cases with expected status codes.
```

## Sequence 6: UI Integration Prompt
Use for demo panel.

```text
Implement a React TypeScript demo panel for personalization output.
Must show:
- active segment
- recommended products
- pricing suggestions
- selected content variant
- trace_id and latency
Keep UI minimal and demo-focused; avoid out-of-scope pages.
```

## Sequence 7: Gate Validation Prompt
Use at each checkpoint.

```text
Run checkpoint validation for phase [name].
Evaluate against CHECKPOINTS.md gate criteria.
Produce:
1) pass/fail for each criterion
2) evidence list (tests/logs/screens)
3) blocker list
4) next actions to reach green
```

## Anti-Drift Prompt
Use if scope creep appears.

```text
Compare current work against REQUIREMENTS.md in-scope/out-of-scope lists.
Flag non-compliant artifacts.
Propose minimal corrective changes to return to scope.
```