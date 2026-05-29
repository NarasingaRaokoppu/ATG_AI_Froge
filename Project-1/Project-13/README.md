# Project 13: N8N Workflow Orchestration

## Goal

Implement an end-to-end N8N workflow that integrates with your existing Project 1 platform and demonstrates course-level complexity:

- Integrates with your chatbot backend (FastAPI)
- Uses your AI stack through Amzur LiteLLM proxy
- Persists workflow history in PostgreSQL
- Calls at least one LangChain-based agent endpoint
- Includes branching, transformation, retries, and validation

## What is Included

This folder contains a complete implementation package for Project 13:

- Prerequisites checklist and setup order
- Plan prompt (for architecture and rollout)
- Execution prompt (for build and validation)
- Importable N8N workflow JSON
- SQL for workflow audit persistence
- Backend endpoint contract mapping to your existing APIs
- N8N environment example

## Directory Layout

```text
Project-13/
  README.md
  prerequisites/
    PROJECT13_PREREQUISITES.md
  prompts/
    PROJECT13_PLAN_PROMPT.md
    PROJECT13_EXECUTION_PROMPT.md
  backend_contract/
    PROJECT13_BACKEND_ENDPOINTS.md
  n8n/
    README.md
    .env.example
    sql/
      001_create_n8n_audit_tables.sql
    workflows/
      project13_daily_chatops_workflow.json
```

## Workflow Use Case

Daily ChatOps Digest and Triage:

1. Trigger at schedule (weekday 9 AM) or webhook.
2. Log in to backend with service account (cookie auth).
3. Fetch chat threads from backend.
4. Transform and filter last 24h activity.
5. Branch:
   - no activity: post low-activity message and write audit
   - activity found: fetch messages, summarize with LiteLLM, classify priority
6. Branch by priority:
   - high: send Slack alert + write audit
   - normal: write Google Sheet + write audit
7. Call agent endpoint (`/api/tic-tac-toe/move`) as required agent integration demo.
8. Persist run details to PostgreSQL for history and observability.

## Complexity Coverage

This implementation includes all six complexity categories:

1. Conditional Logic: no-activity branch and priority branch
2. Data Transformation: normalize payloads, aggregate messages, shape AI output
3. Multiple External Integrations: Slack, Google Sheets, LiteLLM, plus backend APIs
4. Database/File I/O: PostgreSQL audit table writes
5. Error Handling and Retry Logic: retry on HTTP nodes, fallback branch
6. Scheduled or Triggered Execution: Cron and webhook trigger

## Standards Alignment

This package follows `.github/copilot-instructions.md` conventions:

- Uses existing backend routes under `/api/*`
- Uses LiteLLM proxy for AI calls (`litellm.amzur.com`)
- Keeps auth cookie-based for backend integration
- Keeps all Project 13 artifacts isolated in a dedicated folder

## Quick Start

1. Complete all items in `prerequisites/PROJECT13_PREREQUISITES.md`.
2. Create the audit table using `n8n/sql/001_create_n8n_audit_tables.sql`.
3. Configure N8N credentials and env using `n8n/.env.example`.
4. Import `n8n/workflows/project13_daily_chatops_workflow.json` into N8N.
5. Use prompts in `prompts/` for planning and guided execution.
6. Run end-to-end test and capture evidence.
