# Project 13 Backend Contract

This document maps Project 13 workflow steps to existing backend APIs.

## Base URL

- Local example: `http://localhost:8000`
- Health: `GET /health`

## Auth Model

- Backend auth uses JWT in an `httpOnly` cookie.
- N8N must authenticate with `POST /api/auth/login` and reuse `set-cookie` for subsequent `/api/*` calls.

## Endpoint Contracts

### 1) Login

- Method: `POST`
- Path: `/api/auth/login`
- Body:

```json
{
  "email": "service-user@amzur.com",
  "password": "<password>"
}
```

- Success: `200` with user payload and `set-cookie` header.
- Failure handling:
  - `401` invalid credentials -> workflow should fail fast and log audit error.

### 2) List Threads

- Method: `GET`
- Path: `/api/threads`
- Auth: cookie required
- Success: array of thread records.
- Workflow usage:
  - Filter threads for last 24h based on timestamps.
  - Keep top N active threads for message retrieval.

### 3) List Messages for Thread

- Method: `GET`
- Path: `/api/messages/{thread_id}`
- Auth: cookie required
- Success: array of messages for thread.
- Workflow usage:
  - Build conversation text block for summarization.
  - Aggregate by thread before LLM call.

### 4) Agent Integration (Project requirement)

- Method: `POST`
- Path: `/api/tic-tac-toe/move`
- Auth: currently none required by route
- Body:

```json
{
  "board": [null, null, null, null, "X", null, null, null, null]
}
```

- Success: board plus move index.
- Workflow usage:
  - Demonstrate agent endpoint invocation in each run.
  - Persist response in audit metadata.

## LiteLLM Contract

All model calls must go through LiteLLM proxy.

- Method: `POST`
- URL: `https://litellm.amzur.com/chat/completions`
- Headers:
  - `Authorization: Bearer <LITELLM_API_KEY>`
  - `Content-Type: application/json`
- Body (minimum):

```json
{
  "model": "gemini/gemini-2.5-flash",
  "user": "n8n-bot@amzur.com",
  "messages": [
    {"role": "system", "content": "You are a workflow summarizer."},
    {"role": "user", "content": "Summarize these threads..."}
  ],
  "extra_body": {
    "metadata": {
      "application": "amzur-ai-chat",
      "environment": "development"
    }
  }
}
```

## Recommended N8N Retry Policy

Apply to all external HTTP nodes:

- retry on fail: enabled
- max tries: 3
- wait between tries: 2000 ms
- timeout: 30000 ms

## Data Validation Rules for Workflow Input

- Required: `run_source` (`cron` or `webhook`)
- Optional: `lookback_hours` (default 24, min 1, max 168)
- Optional: `top_n_threads` (default 5, min 1, max 20)
- Reject payload when values are out of bounds.

## Expected Failure Modes

1. Backend auth failure -> stop and write audit row with `status=failed`.
2. Empty thread list -> route to no-activity branch.
3. LiteLLM timeout -> retry, then fallback message and audit.
4. Slack/Sheets failure -> continue to DB audit branch with warning status.
