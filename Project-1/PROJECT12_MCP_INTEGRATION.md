# Project 12: MCP Integration (LangGraph)

## Goal

Replace Project 10 hand-written arXiv tool calls with MCP server methods while keeping:

- agent workflow contract unchanged,
- frontend stream handling unchanged,
- system prompt behavior unchanged.

## What changed

### Backend service swap

File: `backend/app/services/research_digest_service.py`

- Replaced direct HTTP + XML arXiv retrieval with MCP calls.
- Uses LangGraph `create_react_agent(...)` and MCP tools exposed by `arxiv-mcp-server`.
- Keeps existing SSE events and payload shape:
  - `status`
  - `query`
  - `papers`
  - `decision`
  - `section`
  - `done`

### New settings

File: `backend/app/core/settings.py`

- `ARXIV_MCP_SERVER_NAME` (default: `arxiv`)
- `ARXIV_MCP_COMMAND` (default: `uvx`)
- `ARXIV_MCP_ARGS` (default: `["arxiv-mcp-server"]`)
- `ARXIV_MCP_TRANSPORT` (default: `stdio`)

### Dependency

File: `backend/requirements.txt`

- Added `langchain-mcp-adapters>=0.1.0`

## MCP server reference

This implementation targets the arXiv MCP server described in:

- https://github.com/blazickjp/arxiv-mcp-server/blob/main/README.md

Primary tool used:

- `search_papers`

## Install and run

From `Project-1/backend`:

```bash
pip install -r requirements.txt
```

Install arXiv MCP server executable (recommended per upstream README):

```bash
uv tool install arxiv-mcp-server
```

Alternative runtime paths are also supported by backend fallback launchers:

- `uvx arxiv-mcp-server`
- `<python> -m arxiv_mcp_server`

## Environment examples

```env
ARXIV_MCP_SERVER_NAME=arxiv
ARXIV_MCP_COMMAND=arxiv-mcp-server
ARXIV_MCP_ARGS=[]
ARXIV_MCP_TRANSPORT=stdio
```

## Validation

- Existing frontend page and stream parser remain unchanged.
- Service-level tests updated for MCP-backed behavior in:
  - `tests/test_research_digest_service.py`

## Notes

- arXiv paper content is untrusted input. Follow MCP security best practices from upstream README.
- If MCP server startup fails, backend returns clear `503` errors with MCP-specific codes.
