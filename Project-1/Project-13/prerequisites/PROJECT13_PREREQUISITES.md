# Project 13 Prerequisites

Use this checklist before importing or executing the Project 13 workflow.

## 1) Core Runtime

- [ ] Python backend (Project 1) is running and reachable (example: `http://localhost:8000`)
- [ ] Frontend is optional for workflow runtime, but backend auth/users must exist
- [ ] N8N is installed and running (local Docker or hosted)
- [ ] PostgreSQL is running and accessible from N8N

## 2) Mandatory Accounts and Credentials

- [ ] N8N service account email/password for backend login (`/api/auth/login`)
- [ ] Slack app token and channel ID (for alerts)
- [ ] Google Sheets credentials and target sheet ID
- [ ] LiteLLM API key for `https://litellm.amzur.com`
- [ ] PostgreSQL credentials for audit writes

## 3) Backend Preconditions (Project 1)

- [ ] Auth routes active:
  - `POST /api/auth/login`
  - `GET /api/auth/me`
- [ ] Thread and message routes active:
  - `GET /api/threads`
  - `GET /api/messages/{thread_id}`
- [ ] Agent route active:
  - `POST /api/tic-tac-toe/move`
- [ ] Health route active:
  - `GET /health`

## 4) Environment Variables

Configure these in N8N or your deployment platform:

- [ ] `BACKEND_BASE_URL` (example: `http://localhost:8000`)
- [ ] `BACKEND_SERVICE_EMAIL`
- [ ] `BACKEND_SERVICE_PASSWORD`
- [ ] `LITELLM_PROXY_URL=https://litellm.amzur.com`
- [ ] `LITELLM_API_KEY`
- [ ] `LITELLM_MODEL=gemini/gemini-2.5-flash`
- [ ] `WORKFLOW_USER_EMAIL=n8n-bot@amzur.com`
- [ ] `SLACK_CHANNEL_ID`
- [ ] `GOOGLE_SHEET_ID`
- [ ] `PGHOST`, `PGPORT`, `PGDATABASE`, `PGUSER`, `PGPASSWORD`

## 5) Database Setup for Workflow Audit

- [ ] Execute `n8n/sql/001_create_n8n_audit_tables.sql`
- [ ] Confirm table exists: `n8n_workflow_run_audit`
- [ ] Confirm insert permission for N8N DB user

## 6) N8N Node Credentials

Create and test these credentials in N8N:

- [ ] HTTP header auth for LiteLLM (`Authorization: Bearer <key>`)
- [ ] Slack credential (bot token)
- [ ] Google Sheets OAuth/service-account credential
- [ ] PostgreSQL credential

## 7) Security and Networking

- [ ] If backend depends on internal network/VPN, ensure N8N can resolve and reach it
- [ ] Do not hardcode secrets in workflow JSON
- [ ] Enable TLS for all non-local URLs
- [ ] Restrict webhook endpoint with secret token and/or IP allowlist

## 8) Validation Data

- [ ] At least one active chat thread with messages in the last 24h
- [ ] At least one thread with low activity to test branch behavior
- [ ] Slack test channel ready
- [ ] Google Sheet tab created for digest logs

## 9) Acceptance Test Checklist

- [ ] Scheduled run executes at expected time
- [ ] Webhook run executes manually with test payload
- [ ] No-activity branch sends fallback output
- [ ] Active branch sends summary to Slack and Sheets
- [ ] AI call includes `user` and metadata payload
- [ ] Agent endpoint call succeeds and result is persisted
- [ ] Audit row written for each run (success/failure)
- [ ] Retry/failure path verified (simulate one HTTP failure)
