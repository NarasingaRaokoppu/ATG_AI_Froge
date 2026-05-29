# N8N Setup for Project 13

## Import Steps

1. Open N8N UI.
2. Import workflow JSON:
   - `n8n/workflows/project13_daily_chatops_workflow.json`
3. Configure all credentials and env placeholders.
4. Activate workflow.

## Required Credentials in N8N

- HTTP credential for LiteLLM bearer token
- Slack credential
- Google Sheets credential
- PostgreSQL credential

## Required Environment Variables

Copy `n8n/.env.example` into your deployment env and populate values.

## Local Test Order

1. Test backend health.
2. Test backend login HTTP node.
3. Test threads and messages HTTP nodes.
4. Test LiteLLM call node.
5. Test Slack/Sheets nodes.
6. Test PostgreSQL audit insert.
7. Trigger full workflow via webhook.
8. Verify scheduled trigger run.

## Notes

- Keep credentials out of workflow JSON.
- If backend runs on a different host from N8N Docker, use host-resolvable URL (not localhost from container perspective).
- If your org network requires VPN for internal services, ensure N8N runtime has that network access.
