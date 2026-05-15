"""Research digest agent that searches arXiv and streams structured output."""

from __future__ import annotations

import asyncio
import json
import re
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from typing import Any
from xml.etree import ElementTree

import httpx
from fastapi import HTTPException, status

from app.ai.llm import llm
from app.core import settings
from app.schemas.research_digest import (
    ResearchDigestDecision,
    ResearchDigestRequest,
    ResearchDigestResponse,
    ResearchDigestSection,
    ResearchPaper,
)

_ATOM_NS = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
_DEFAULT_MAX_ROUNDS = 3
_DEFAULT_PAPERS_PER_ROUND = 5
_ARXIV_MAX_RETRIES = 3
_ARXIV_RETRY_BACKOFF_SECONDS = 2.0
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


def parse_arxiv_feed(xml_text: str) -> list[ResearchPaper]:
    """Parse the arXiv Atom response into normalized paper records."""
    root = ElementTree.fromstring(xml_text)
    papers: list[ResearchPaper] = []

    for entry in root.findall("atom:entry", _ATOM_NS):
        raw_id = entry.findtext("atom:id", default="", namespaces=_ATOM_NS).strip()
        arxiv_id = raw_id.rsplit("/", 1)[-1]
        title = _compact_whitespace(entry.findtext("atom:title", default="", namespaces=_ATOM_NS))
        summary = _compact_whitespace(entry.findtext("atom:summary", default="", namespaces=_ATOM_NS))
        authors = [
            _compact_whitespace(author.findtext("atom:name", default="", namespaces=_ATOM_NS))
            for author in entry.findall("atom:author", _ATOM_NS)
            if _compact_whitespace(author.findtext("atom:name", default="", namespaces=_ATOM_NS))
        ]
        category = entry.find("arxiv:primary_category", _ATOM_NS)
        pdf_url: str | None = None
        for link in entry.findall("atom:link", _ATOM_NS):
            if link.attrib.get("title") == "pdf" or link.attrib.get("type") == "application/pdf":
                pdf_url = link.attrib.get("href")
                break

        if not arxiv_id or not title:
            continue

        papers.append(
            ResearchPaper(
                arxiv_id=arxiv_id,
                title=title,
                authors=authors,
                summary=summary,
                published=_parse_iso8601(entry.findtext("atom:published", namespaces=_ATOM_NS)),
                updated=_parse_iso8601(entry.findtext("atom:updated", namespaces=_ATOM_NS)),
                primary_category=category.attrib.get("term") if category is not None else None,
                pdf_url=pdf_url,
                abs_url=raw_id,
            )
        )

    return papers


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
    params = {
        "search_query": query,
        "start": 0,
        "max_results": max_results,
        "sortBy": "relevance",
        "sortOrder": "descending",
    }
    headers = {"User-Agent": settings.ARXIV_USER_AGENT}
    timeout = httpx.Timeout(settings.RESEARCH_DIGEST_TIMEOUT_SECONDS)
    async with httpx.AsyncClient(timeout=timeout, headers=headers) as client:
        for attempt in range(1, _ARXIV_MAX_RETRIES + 1):
            try:
                response = await client.get(settings.ARXIV_API_URL, params=params)
                response.raise_for_status()
                return parse_arxiv_feed(response.text)
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code != status.HTTP_429_TOO_MANY_REQUESTS:
                    raise

                if attempt >= _ARXIV_MAX_RETRIES:
                    raise HTTPException(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail={
                            "error": "arxiv_rate_limited",
                            "message": (
                                "arXiv is rate-limiting requests right now. "
                                "Please wait a moment and try again."
                            ),
                        },
                    ) from exc

                retry_after_header = exc.response.headers.get("Retry-After")
                retry_after_seconds = _ARXIV_RETRY_BACKOFF_SECONDS * attempt
                if retry_after_header:
                    try:
                        retry_after_seconds = max(
                            retry_after_seconds,
                            float(retry_after_header),
                        )
                    except ValueError:
                        pass
                await asyncio.sleep(retry_after_seconds)
            except httpx.RequestError as exc:
                if attempt >= _ARXIV_MAX_RETRIES:
                    raise HTTPException(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail={
                            "error": "arxiv_unavailable",
                            "message": (
                                "Unable to reach arXiv right now. "
                                "Please try again shortly."
                            ),
                        },
                    ) from exc
                await asyncio.sleep(_ARXIV_RETRY_BACKOFF_SECONDS * attempt)

    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail={
            "error": "arxiv_unavailable",
            "message": "Unable to reach arXiv right now. Please try again shortly.",
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
