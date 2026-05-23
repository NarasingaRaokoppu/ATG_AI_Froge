import pytest
from fastapi import HTTPException

from app.services.research_digest_service import _fallback_query, _search_arxiv


def test_fallback_query_preserves_topic_and_missing_angles() -> None:
    query = _fallback_query(
        "retrieval augmented generation for legal research",
        ["enterprise deployments"],
    )

    assert 'all:"retrieval augmented generation for legal research"' in query
    assert 'all:"enterprise deployments"' in query


@pytest.mark.asyncio
async def test_search_arxiv_normalizes_mcp_tool_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_run_search_tool_via_langgraph(*, query: str, max_results: int):
        assert query == 'all:"llm safety"'
        assert max_results == 5
        return {
            "papers": [
                {
                    "paper_id": "2501.12345v1",
                    "title": "MCP Driven Retrieval for Agentic Workflows",
                    "authors": [{"name": "Alice Smith"}, {"name": "Bob Jones"}],
                    "abstract": "Combines MCP tools with orchestrated agent loops.",
                    "published": "2025-01-09T09:30:00Z",
                    "updated": "2025-01-10T12:00:00Z",
                    "primary_category": "cs.AI",
                    "pdf_url": "https://arxiv.org/pdf/2501.12345v1",
                    "abs_url": "https://arxiv.org/abs/2501.12345v1",
                }
            ]
        }

    monkeypatch.setattr(
        "app.services.research_digest_service._run_search_tool_via_langgraph",
        fake_run_search_tool_via_langgraph,
    )

    papers = await _search_arxiv('all:"llm safety"', 5)

    assert len(papers) == 1
    assert papers[0].arxiv_id == "2501.12345v1"
    assert papers[0].title == "MCP Driven Retrieval for Agentic Workflows"
    assert papers[0].authors == ["Alice Smith", "Bob Jones"]
    assert papers[0].summary == "Combines MCP tools with orchestrated agent loops."
    assert papers[0].primary_category == "cs.AI"


@pytest.mark.asyncio
async def test_search_arxiv_returns_clear_error_when_mcp_payload_empty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_run_search_tool_via_langgraph(*, query: str, max_results: int):
        return {"papers": []}

    monkeypatch.setattr(
        "app.services.research_digest_service._run_search_tool_via_langgraph",
        fake_run_search_tool_via_langgraph,
    )

    with pytest.raises(HTTPException) as exc_info:
        await _search_arxiv('all:"retry failure"', 5)

    assert exc_info.value.status_code == 503
    assert exc_info.value.detail["error"] == "arxiv_mcp_empty"
