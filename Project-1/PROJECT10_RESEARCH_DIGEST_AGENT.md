# Project 10: Research Digest Agent

## Goal

Build a full-stack AI agent that:

- searches arXiv iteratively
- decides when it has enough evidence
- streams a structured research digest to the browser in real time

## Backend

- Route: `POST /api/research-digest/stream`
- Auth: same cookie-based auth as the rest of the app
- Input:
  - `topic`
- Internal agent defaults:
   - search rounds are fixed in the backend
   - papers fetched per round are fixed in the backend
- SSE events:
  - `status`
  - `query`
  - `papers`
  - `decision`
  - `section`
  - `done`
  - `error`

## Frontend

- Route: `/research-digest`
- Capabilities:
   - submit a topic
  - watch search rounds and evidence decisions live
  - inspect collected papers
  - read structured digest sections as they arrive
  - cancel an active run

## Required Scenarios

1. Happy path
   - User enters a topic and gets multiple arXiv papers, an evidence sufficiency decision, and final digest sections.

2. Enough evidence after first round
   - Agent should stop early when the evidence is already broad and coherent.

3. Evidence not sufficient
   - Agent should issue another arXiv query with refined search intent and continue until its internal round limit or sufficiency.

4. No arXiv results
   - Backend should emit an `error` event and frontend should show a readable error state.

5. Duplicate papers across rounds
   - Frontend should keep a deduplicated evidence stack.

6. User cancellation
   - Frontend should abort the request and stop streaming without breaking navigation.

7. Auth protection
   - Unauthenticated users should not be able to access the route successfully.

8. Cross-project navigation
   - From chat, users should be able to open Projects 8, 9, and 10 directly.

## How To Test

### Backend helper test

From `Project-1/backend`:

```powershell
pytest D:\ATG_Forge\ATG_AI_Froge\Project-1\tests\test_research_digest_service.py
```

### Manual end-to-end

1. Start backend and frontend.
2. Log in.
3. Open `/research-digest`.
4. Run a topic such as `agentic RAG evaluation`.
5. Confirm the UI receives status, query, papers, decision, and section updates.
6. Open a second run with a very narrow topic to verify multiple rounds.
7. Try cancelling during section generation.
8. Return to `/chat` and verify the navigation links still open Projects 8, 9, and 10.

### Suggested manual topics

- `agentic retrieval augmented generation for enterprise support`
- `multimodal RAG benchmark evaluation`
- `LLM groundedness verification in knowledge-intensive QA`
- `small language models for on-device agents`
