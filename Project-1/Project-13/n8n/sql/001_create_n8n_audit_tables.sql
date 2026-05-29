CREATE TABLE IF NOT EXISTS n8n_workflow_run_audit (
    id UUID PRIMARY KEY,
    workflow_name VARCHAR(128) NOT NULL,
    run_source VARCHAR(32) NOT NULL,
    run_started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    run_finished_at TIMESTAMPTZ,
    status VARCHAR(32) NOT NULL,
    processed_threads INTEGER NOT NULL DEFAULT 0,
    high_priority_threads INTEGER NOT NULL DEFAULT 0,
    summary_text TEXT,
    agent_result JSONB,
    error_code VARCHAR(64),
    error_message TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS ix_n8n_workflow_run_audit_started_at
ON n8n_workflow_run_audit (run_started_at DESC);

CREATE INDEX IF NOT EXISTS ix_n8n_workflow_run_audit_status
ON n8n_workflow_run_audit (status);
