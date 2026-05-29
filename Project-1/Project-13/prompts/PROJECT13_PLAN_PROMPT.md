# Project 13 Plan Prompt (End-to-End)

Use this prompt with Copilot/LLM to produce the implementation plan before execution.

---

You are designing Project 13 for an existing platform called Amzur AI Chat.

Context:
- Projects 1-12 are implemented.
- Backend stack: FastAPI + LangChain + PostgreSQL.
- Auth: cookie-based JWT (`httpOnly`).
- AI gateway: all model calls must use `https://litellm.amzur.com`.
- Existing backend endpoints include:
  - `POST /api/auth/login`
  - `GET /api/threads`
  - `GET /api/messages/{thread_id}`
  - `POST /api/tic-tac-toe/move`
  - `GET /health`
- Existing coding standards are defined in `.github/copilot-instructions.md`.

Task:
Create a detailed implementation plan for Project 13 (N8N Workflow) with a real business use case.
The plan must satisfy submission complexity and quality criteria.

Mandatory requirements:
1. Include at least 3 complexity features (target all 6 if possible):
   - conditional logic with 2+ branches
   - data transformation
   - multiple external integrations
   - DB/file I/O
   - error handling and retry
   - scheduled or triggered execution
2. Integrate with systems built in prior projects:
   - chatbot backend APIs
   - PostgreSQL data persistence
   - LiteLLM AI call
   - at least one agent endpoint
3. Include security considerations:
   - secrets management
   - input validation
   - auth/cookie handling for backend calls
4. Include testing plan and failure-mode test matrix.
5. Include rollout plan with phases and effort estimate.

Output format:
- Section 1: Use-case statement and business value
- Section 2: Architecture (trigger, branches, integrations)
- Section 3: Node-by-node workflow design
- Section 4: Data contracts (input/output schemas)
- Section 5: Error handling and retry strategy
- Section 6: Security controls
- Section 7: Test plan (happy path + failure path)
- Section 8: Deployment/runbook
- Section 9: Submission checklist mapping

Constraints:
- Use Gemini model via LiteLLM proxy (not direct provider endpoint).
- Keep backend integration aligned with existing API routes.
- Keep all Project 13 assets under a dedicated `Project-13/` folder.
- Do not propose architecture that bypasses current auth model.

Deliver a concrete, executable plan, not a generic explanation.
