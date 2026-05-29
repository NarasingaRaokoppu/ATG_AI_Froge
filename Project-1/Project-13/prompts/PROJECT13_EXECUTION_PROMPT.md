# Project 13 Execution Prompt (End-to-End)

Use this prompt to execute implementation tasks and produce final deliverables.

---

You are implementing Project 13 in an existing repository.

Repository facts:
- Backend: FastAPI + LangChain + PostgreSQL
- Frontend: React + TypeScript
- AI gateway: `https://litellm.amzur.com` only
- Existing backend endpoints to integrate:
  - `POST /api/auth/login`
  - `GET /api/threads`
  - `GET /api/messages/{thread_id}`
  - `POST /api/tic-tac-toe/move`
  - `GET /health`
- Standards file: `.github/copilot-instructions.md`

Primary objective:
Implement Project 13 as a production-style N8N workflow package under `Project-13/` with docs, workflow JSON, setup SQL, and test/runbook instructions.

Implementation tasks:
1. Create folder structure:
   - `Project-13/prerequisites/`
   - `Project-13/prompts/`
   - `Project-13/backend_contract/`
   - `Project-13/n8n/workflows/`
   - `Project-13/n8n/sql/`
2. Create prerequisite checklist markdown.
3. Create backend contract markdown (endpoint references, payload expectations, auth notes).
4. Create N8N workflow JSON that includes:
   - Cron or webhook trigger
   - Input validation and data transformation node
   - Backend login and cookie reuse
   - Backend threads/messages ingestion
   - LiteLLM summarization call using `gemini/gemini-2.5-flash`
   - Branching (no activity vs activity, and high vs normal priority)
   - Slack and Google Sheets integrations
   - PostgreSQL audit write
   - Agent endpoint call (`/api/tic-tac-toe/move`)
   - Retry/fallback behavior
5. Create SQL file for audit table.
6. Create N8N env example.
7. Create Project 13 README with setup, import, test, and submission checklist mapping.

Quality constraints:
- Must satisfy complexity criteria from the assignment.
- Must include meaningful business logic (not toy workflow).
- Must include explicit failure-mode behavior.
- Must include data validation rules.
- Must be import-friendly into N8N with clear placeholders for credentials.

Output expectations:
- Return changed file list.
- Provide a short execution summary.
- Provide exact next commands/actions for user to run in order.
