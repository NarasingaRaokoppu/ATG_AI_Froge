import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.api.routes.tic_tac_toe import BoardRequest


PROJECT_13_DIR = Path(__file__).resolve().parents[1] / "Project-13"
WORKFLOW_PATH = PROJECT_13_DIR / "n8n" / "workflows" / "project13_daily_chatops_workflow.json"
SQL_PATH = PROJECT_13_DIR / "n8n" / "sql" / "001_create_n8n_audit_tables.sql"


@pytest.fixture(scope="module")
def workflow() -> dict:
    return json.loads(WORKFLOW_PATH.read_text(encoding="utf-8"))


def _node_map(workflow: dict) -> dict[str, dict]:
    return {node["name"]: node for node in workflow["nodes"]}


def test_project13_workflow_contains_required_contract_nodes(workflow: dict) -> None:
    nodes = _node_map(workflow)

    assert "Backend Login" in nodes
    assert "Get Threads" in nodes
    assert "Get Top Thread Messages" in nodes
    assert "LiteLLM Summarize" in nodes
    assert "Agent Call" in nodes
    assert "Build Audit Payload" in nodes
    assert "LLM Response OK?" in nodes
    assert "Build Fallback Summary" in nodes
    assert "Write Audit Success" in nodes
    assert "Write Audit No Activity" in nodes


def test_project13_workflow_includes_retry_timeout_on_http_nodes(workflow: dict) -> None:
    nodes = _node_map(workflow)
    http_node_names = [
        "Backend Login",
        "Get Threads",
        "Get Top Thread Messages",
        "LiteLLM Summarize",
        "Agent Call",
    ]

    for name in http_node_names:
        options = nodes[name]["parameters"]["options"]
        assert options["timeout"] == 30000
        assert options["retry"]["enabled"] is True
        assert options["retry"]["maxTries"] >= 2


def test_project13_workflow_normalize_input_rejects_out_of_bounds(workflow: dict) -> None:
    nodes = _node_map(workflow)
    code = nodes["Normalize Input"]["parameters"]["jsCode"]

    assert "Invalid run_source" in code
    assert "Invalid lookback_hours" in code
    assert "Invalid top_n_threads" in code


def test_project13_workflow_contains_step_explanation_notes(workflow: dict) -> None:
    note_nodes = [
        node
        for node in workflow["nodes"]
        if node.get("type") == "n8n-nodes-base.stickyNote"
    ]

    assert len(note_nodes) >= 2


def test_project13_workflow_has_explicit_llm_fallback_connection(workflow: dict) -> None:
    llm_branch = workflow["connections"]["LLM Response OK?"]["main"]

    assert llm_branch[0][0]["node"] == "Parse Summary"
    assert llm_branch[1][0]["node"] == "Build Fallback Summary"


def test_project13_sql_audit_table_has_required_columns() -> None:
    sql_text = SQL_PATH.read_text(encoding="utf-8")

    assert "CREATE TABLE IF NOT EXISTS n8n_workflow_run_audit" in sql_text
    assert "status VARCHAR(32) NOT NULL" in sql_text
    assert "processed_threads INTEGER NOT NULL DEFAULT 0" in sql_text
    assert "high_priority_threads INTEGER NOT NULL DEFAULT 0" in sql_text
    assert "agent_result JSONB" in sql_text
    assert "metadata JSONB NOT NULL DEFAULT '{}'::jsonb" in sql_text


def test_project13_board_request_rejects_invalid_shape() -> None:
    with pytest.raises(ValidationError):
        BoardRequest(board=[None] * 8)

    with pytest.raises(ValidationError):
        BoardRequest(board=["A"] * 9)

    valid = BoardRequest(board=[None, None, None, None, "X", None, None, None, None])
    assert len(valid.board) == 9
