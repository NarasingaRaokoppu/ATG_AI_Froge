import pytest
from fastapi import HTTPException

from app.services.research_digest_service import _parse_mcp_args


def test_project12_parse_mcp_args_rejects_invalid_json() -> None:
    with pytest.raises(HTTPException) as exc_info:
        _parse_mcp_args("not-json")

    assert exc_info.value.status_code == 500
    assert exc_info.value.detail["error"] == "invalid_mcp_args"


def test_project12_parse_mcp_args_rejects_non_string_array() -> None:
    with pytest.raises(HTTPException) as exc_info:
        _parse_mcp_args('["ok", 123]')

    assert exc_info.value.status_code == 500
    assert exc_info.value.detail["error"] == "invalid_mcp_args"


def test_project12_parse_mcp_args_accepts_string_array() -> None:
    args = _parse_mcp_args('["arxiv-mcp-server", "--transport", "stdio"]')
    assert args == ["arxiv-mcp-server", "--transport", "stdio"]
