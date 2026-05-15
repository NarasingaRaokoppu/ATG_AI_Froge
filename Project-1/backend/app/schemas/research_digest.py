"""Schemas for the Project 10 research digest agent."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ResearchDigestRequest(BaseModel):
    """Client payload for a research digest run."""

    topic: str = Field(min_length=5, max_length=300)


class ResearchPaper(BaseModel):
    """Normalized arXiv paper metadata."""

    arxiv_id: str
    title: str
    authors: list[str] = Field(default_factory=list)
    summary: str
    published: datetime
    updated: datetime
    primary_category: str | None = None
    pdf_url: str | None = None
    abs_url: str


class ResearchDigestDecision(BaseModel):
    """Evidence sufficiency decision after a search round."""

    enough_evidence: bool
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str
    missing_angles: list[str] = Field(default_factory=list)


class ResearchDigestSection(BaseModel):
    """A single digest section streamed to the frontend."""

    id: str
    title: str
    content: str


class ResearchDigestResponse(BaseModel):
    """Final structured digest payload."""

    topic: str
    executed_queries: list[str] = Field(default_factory=list)
    rounds_completed: int
    papers: list[ResearchPaper] = Field(default_factory=list)
    decision: ResearchDigestDecision
    sections: list[ResearchDigestSection] = Field(default_factory=list)
