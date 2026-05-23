"""Research digest agent that searches arXiv and streams structured output."""

from __future__ import annotations

import ast
import json
import re
import sys
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from typing import Any

from fastapi import HTTPException, status
from langgraph.prebuilt import create_react_agent

try:
    from langchain_mcp_adapters.client import MultiServerMCPClient
except Exception:  # pragma: no cover - handled with runtime error message
    MultiServerMCPClient = None

from app.ai.llm import llm
from app.core import settings
from app.schemas.research_digest import (
    ResearchDigestDecision,
    ResearchDigestRequest,
    ResearchDigestResponse,
    ResearchDigestSection,
    ResearchPaper,
)

_DEFAULT_MAX_ROUNDS = 3
_DEFAULT_PAPERS_PER_ROUND = 5
_MCP_SEARCH_TOOL = "search_papers"
_SECTION_SPECS: tuple[tuple[str, str, str], ...] = (
    (
        "executive-summary",
        "Executive Summary",
        "Summarize the topic landscape in 5-7 sentences. State the dominant direction, where the evidence is strong, and where it is still thin.",
    ),
    (
        "key-findings",
        "Key Findings",
        "Write 4-6 bullet points. Each bullet must mention at least one paper title or arXiv id and explain why it matters.",
    ),
    (
        "methods-trends",
        "Methods and Benchmarks",
        "Explain the recurring methods, datasets, benchmarks, or evaluation patterns that appear across the papers.",
    ),
    (
        "gaps-next-steps",
        "Gaps and Next Steps",
        "Highlight contradictions, underexplored areas, and practical next reading steps. End with 3 concrete follow-up questions.",
    ),
)


def _coerce_text(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        parts: list[str] = []
        for item in value:
            if isinstance(item, str):
                parts.append(item)
                continue
            if isinstance(item, dict):
                text = item.get("text")
                if isinstance(text, str):
                    parts.append(text)
        return "\n".join(part.strip() for part in parts if part.strip()).strip()
    return str(value).strip()


def _strip_code_fences(raw: str) -> str:
    text = raw.strip()
    if not text.startswith("```"):
        return text

    lines = text.splitlines()
    if len(lines) >= 3 and lines[-1].strip() == "```":
        return "\n".join(lines[1:-1]).strip()
    return text


def _compact_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _fallback_query(topic: str, missing_angles: list[str]) -> str:
    parts = [_compact_whitespace(topic)]
    parts.extend(_compact_whitespace(item) for item in missing_angles[:2] if item.strip())
    quoted = [f'all:"{part.replace("\"", "")[:120]}"' for part in parts if part]
    return " AND ".join(quoted) if quoted else 'all:"research survey"'


def _parse_iso8601(value: str | None) -> datetime:
    if not value:
        return datetime.now(tz=UTC)
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _json_or_literal(value: str) -> Any:
    text = _strip_code_fences(value)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return ast.literal_eval(text)


def _parse_mcp_args(raw_args: str) -> list[str]:
    try:
        parsed = json.loads(raw_args)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "invalid_mcp_args",
                "message": "ARXIV_MCP_ARGS must be valid JSON array syntax.",
            },
        ) from exc

    if not isinstance(parsed, list) or not all(isinstance(item, str) for item in parsed):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "invalid_mcp_args",
                "message": "ARXIV_MCP_ARGS must decode to a list of strings.",
            },
        )
    return parsed


def _normalize_authors(raw_authors: Any) -> list[str]:
    if isinstance(raw_authors, list):
        normalized: list[str] = []
        for author in raw_authors:
            if isinstance(author, str) and author.strip():
                normalized.append(author.strip())
                continue
            if isinstance(author, dict):
                name = author.get("name")
                if isinstance(name, str) and name.strip():
                    normalized.append(name.strip())
        return normalized
    return []


def _extract_entries(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [entry for entry in payload if isinstance(entry, dict)]

    if isinstance(payload, dict):
        for key in ("papers", "results", "items", "entries", "data"):
            value = payload.get(key)
            if isinstance(value, list):
                return [entry for entry in value if isinstance(entry, dict)]
            if isinstance(value, dict):
                nested = _extract_entries(value)
                if nested:
                    return nested
    return []


def _normalize_mcp_search_payload(payload: Any) -> list[ResearchPaper]:
    papers: list[ResearchPaper] = []
    for item in _extract_entries(payload):
        raw_id = str(
            item.get("paper_id")
            or item.get("arxiv_id")
            or item.get("id")
            or item.get("identifier")
            or ""
        ).strip()
        arxiv_id = raw_id.rsplit("/", 1)[-1]

        title = _compact_whitespace(str(item.get("title") or ""))
        if not arxiv_id or not title:
            continue

        summary = _compact_whitespace(str(item.get("summary") or item.get("abstract") or ""))
        published = _parse_iso8601(str(item.get("published") or item.get("submitted") or ""))
        updated = _parse_iso8601(str(item.get("updated") or item.get("published") or ""))
        categories = item.get("categories")
        primary_category = item.get("primary_category")
        if not primary_category and isinstance(categories, list) and categories:
            first = categories[0]
            if isinstance(first, str):
                primary_category = first

        pdf_url = item.get("pdf_url") or item.get("pdf")
        abs_url = item.get("abs_url") or item.get("url") or f"https://arxiv.org/abs/{arxiv_id}"

        papers.append(
            ResearchPaper(
                arxiv_id=arxiv_id,
                title=title,
                authors=_normalize_authors(item.get("authors")),
                summary=summary,
                published=published,
                updated=updated,
                primary_category=primary_category if isinstance(primary_category, str) else None,
                pdf_url=pdf_url if isinstance(pdf_url, str) else None,
                abs_url=abs_url if isinstance(abs_url, str) else f"https://arxiv.org/abs/{arxiv_id}",
            )
        )
    return papers


def _coerce_structured_content(value: Any) -> Any:
    if isinstance(value, dict):
        return value
    if isinstance(value, list):
        merged = _coerce_text(value)
        if merged:
            return _json_or_literal(merged)
        return value
    if isinstance(value, str):
        return _json_or_literal(value)
    raise ValueError("Unable to decode MCP tool content")


def _extract_mcp_tool_payload(messages: list[Any]) -> Any:
    for message in reversed(messages):
        name = getattr(message, "name", "")
        if name != _MCP_SEARCH_TOOL:
            continue
        return _coerce_structured_content(getattr(message, "content", ""))

    if messages:
        return _coerce_structured_content(getattr(messages[-1], "content", ""))
    raise ValueError("No MCP messages returned")


async def _run_search_tool_via_langgraph(*, query: str, max_results: int) -> Any:
    if MultiServerMCPClient is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "missing_mcp_dependency",
                "message": "Install langchain-mcp-adapters to enable Project 12 MCP integration.",
            },
        )

    configured_args = _parse_mcp_args(settings.ARXIV_MCP_ARGS)
    candidate_launchers = [
        (settings.ARXIV_MCP_COMMAND, configured_args),
        ("arxiv-mcp-server", []),
        (sys.executable, ["-m", "arxiv_mcp_server"]),
    ]

    last_error: Exception | None = None
    for index, (command, args) in enumerate(candidate_launchers):
        mcp_client = MultiServerMCPClient(
            {
                settings.ARXIV_MCP_SERVER_NAME: {
                    "command": command,
                    "args": args,
                    "transport": settings.ARXIV_MCP_TRANSPORT,
                }
            }
        )
        try:
            tools = await mcp_client.get_tools()
            if not tools:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail={
                        "error": "mcp_tools_unavailable",
                        "message": "Connected to MCP server but no tools were exposed.",
                    },
                )

            agent = create_react_agent(model=llm, tools=tools)
            response = await agent.ainvoke(
                {
                    "messages": [
                        (
                            "system",
                            "You are an arXiv retrieval worker. Call the search_papers MCP tool exactly once. "
                            "Then return only raw JSON from the tool response with no markdown and no explanation.",
                        ),
                        (
                            "human",
                            f"query={query}\nmax_results={max_results}\nsort_by=relevance",
                        ),
                    ]
                }
            )
            messages = response.get("messages", []) if isinstance(response, dict) else []
            try:
                return _extract_mcp_tool_payload(messages)
            except Exception:
                # If the LLM does not surface tool output in a parseable shape, call the tool directly.
                search_tool = next((tool for tool in tools if getattr(tool, "name", "") == _MCP_SEARCH_TOOL), None)
                if search_tool is None:
                    raise
                return await search_tool.ainvoke(
                    {
                        "query": query,
                        "max_results": max_results,
                        "sort_by": "relevance",
                    }
                )
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            if index == len(candidate_launchers) - 1:
                break
        finally:
            aclose = getattr(mcp_client, "aclose", None)
            if callable(aclose):
                await aclose()

    if isinstance(last_error, HTTPException):
        raise last_error
    raise RuntimeError(f"Unable to start MCP launcher candidates: {last_error}")


def _paper_digest_brief(papers: list[ResearchPaper]) -> str:
    lines: list[str] = []
    for index, paper in enumerate(papers, start=1):
        authors = ", ".join(paper.authors[:3]) or "Unknown authors"
        if len(paper.authors) > 3:
            authors += ", et al."
        summary = paper.summary[:500]
        lines.append(
            f"{index}. [{paper.arxiv_id}] {paper.title} ({paper.published.year}) | "
            f"Authors: {authors} | Category: {paper.primary_category or 'n/a'} | Summary: {summary}"
        )
    return "\n".join(lines)


async def _generate_search_query(
    *,
    topic: str,
    previous_queries: list[str],
    papers: list[ResearchPaper],
    missing_angles: list[str],
    round_number: int,
) -> str:
    fallback = _fallback_query(topic, missing_angles)
    if round_number == 1:
        return fallback

    prompt = f"""
You are planning the next arXiv search query for a research agent.

Topic: {topic}
Round: {round_number}
Previous queries: {previous_queries or ['None']}
Missing angles: {missing_angles or ['None']}

Current evidence:
{_paper_digest_brief(papers[-6:]) if papers else 'No papers collected yet.'}

Return exactly one arXiv API search_query string.
Rules:
- Prefer arXiv field syntax like all:, ti:, abs:, cat:.
- Keep it under 18 terms.
- No markdown, no explanation, no quotes around the whole answer.
"""
    response = await llm.ainvoke(prompt)
    raw = _coerce_text(getattr(response, "content", response))
    query = _compact_whitespace(raw.splitlines()[0] if raw else fallback)
    return query[:240] if query else fallback


async def _search_arxiv(query: str, max_results: int) -> list[ResearchPaper]:
    try:
        payload = await _run_search_tool_via_langgraph(query=query, max_results=max_results)
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "arxiv_mcp_unavailable",
                "message": "Unable to query arXiv MCP server right now. Please try again shortly.",
            },
        ) from exc

    papers = _normalize_mcp_search_payload(payload)
    if papers:
        return papers[:max_results]

    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail={
            "error": "arxiv_mcp_empty",
            "message": "MCP search returned no usable papers for this query.",
        },
    )


def _fallback_decision(*, paper_count: int, round_number: int, max_rounds: int) -> ResearchDigestDecision:
    enough = paper_count >= 6 or round_number >= max_rounds
    confidence = 0.85 if paper_count >= 8 else 0.7 if enough else 0.45
    rationale = (
        "Collected enough distinct papers to produce a useful digest."
        if enough
        else "Evidence is still narrow; another search round should improve coverage."
    )
    missing = [] if enough else ["Alternative methods", "Recent benchmarks", "Failure cases"]
    return ResearchDigestDecision(
        enough_evidence=enough,
        confidence=confidence,
        rationale=rationale,
        missing_angles=missing,
    )


async def _assess_evidence(
    *,
    topic: str,
    papers: list[ResearchPaper],
    round_number: int,
    max_rounds: int,
) -> ResearchDigestDecision:
    if not papers:
        return _fallback_decision(paper_count=0, round_number=round_number, max_rounds=max_rounds)

    prompt = f"""
You are deciding whether a research agent has enough evidence to write a digest.

Topic: {topic}
Round: {round_number} of {max_rounds}

Evidence set:
{_paper_digest_brief(papers[:8])}

Return strict JSON with this shape:
{{
  "enough_evidence": true,
  "confidence": 0.0,
  "rationale": "short explanation",
  "missing_angles": ["angle 1", "angle 2"]
}}

Use confidence between 0 and 1. If the evidence is narrow, contradictory, or repetitive, set enough_evidence to false.
"""
    try:
        response = await llm.ainvoke(prompt)
        raw = _strip_code_fences(_coerce_text(getattr(response, "content", response)))
        parsed = json.loads(raw)
        return ResearchDigestDecision.model_validate(parsed)
    except Exception:  # noqa: BLE001
        return _fallback_decision(
            paper_count=len(papers),
            round_number=round_number,
            max_rounds=max_rounds,
        )


async def _build_section(
    *,
    topic: str,
    papers: list[ResearchPaper],
    decision: ResearchDigestDecision,
    title: str,
    instruction: str,
) -> str:
    prompt = f"""
Write the '{title}' section of a research digest.

Topic: {topic}
Evidence sufficiency rationale: {decision.rationale}

Papers:
{_paper_digest_brief(papers[:10])}

Instructions:
{instruction}

Requirements:
- Be concise but specific.
- Cite papers inline using [arXiv:{papers[0].arxiv_id}] style whenever possible.
- Do not invent results that are not grounded in the papers.
- Output only the section body.
"""
    response = await llm.ainvoke(prompt)
    return _coerce_text(getattr(response, "content", response))


async def stream_research_digest(
    payload: ResearchDigestRequest,
) -> AsyncGenerator[dict[str, Any], None]:
    """Stream the full research digest workflow as SSE events."""
    collected: dict[str, ResearchPaper] = {}
    executed_queries: list[str] = []
    missing_angles: list[str] = []
    decision = _fallback_decision(
        paper_count=0,
        round_number=0,
        max_rounds=_DEFAULT_MAX_ROUNDS,
    )

    for round_number in range(1, _DEFAULT_MAX_ROUNDS + 1):
        yield {"event": "status", "data": f"Searching arXiv (round {round_number}/{_DEFAULT_MAX_ROUNDS})"}
        query = await _generate_search_query(
            topic=payload.topic,
            previous_queries=executed_queries,
            papers=list(collected.values()),
            missing_angles=missing_angles,
            round_number=round_number,
        )
        executed_queries.append(query)
        yield {"event": "query", "data": {"round": round_number, "query": query}}

        papers = await _search_arxiv(query, _DEFAULT_PAPERS_PER_ROUND)
        new_papers: list[ResearchPaper] = []
        for paper in papers:
            if paper.arxiv_id in collected:
                continue
            collected[paper.arxiv_id] = paper
            new_papers.append(paper)

        yield {
            "event": "papers",
            "data": {
                "round": round_number,
                "query": query,
                "new_count": len(new_papers),
                "papers": [paper.model_dump(mode="json") for paper in new_papers],
            },
        }

        ranked_papers = sorted(collected.values(), key=lambda item: item.published, reverse=True)
        decision = await _assess_evidence(
            topic=payload.topic,
            papers=ranked_papers,
            round_number=round_number,
            max_rounds=_DEFAULT_MAX_ROUNDS,
        )
        missing_angles = decision.missing_angles
        yield {
            "event": "decision",
            "data": {
                "round": round_number,
                "paper_count": len(ranked_papers),
                **decision.model_dump(mode="json"),
            },
        }

        if decision.enough_evidence:
            break

    final_papers = sorted(collected.values(), key=lambda item: item.published, reverse=True)
    if not final_papers:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "error": "arxiv_empty",
                "message": "No arXiv papers were returned for the requested topic.",
            },
        )

    yield {"event": "status", "data": "Compiling structured digest"}
    sections: list[ResearchDigestSection] = []
    for section_id, section_title, instruction in _SECTION_SPECS:
        yield {"event": "status", "data": f"Writing {section_title}"}
        content = await _build_section(
            topic=payload.topic,
            papers=final_papers,
            decision=decision,
            title=section_title,
            instruction=instruction,
        )
        section = ResearchDigestSection(id=section_id, title=section_title, content=content)
        sections.append(section)
        yield {"event": "section", "data": section.model_dump(mode="json")}

    response = ResearchDigestResponse(
        topic=payload.topic,
        executed_queries=executed_queries,
        rounds_completed=len(executed_queries),
        papers=final_papers,
        decision=decision,
        sections=sections,
    )
    yield {"event": "done", "data": response.model_dump(mode="json")}
