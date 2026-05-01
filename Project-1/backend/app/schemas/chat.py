"""Pydantic schemas for chat endpoints."""

from uuid import UUID

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Incoming chat message payload."""

    message: str = Field(..., min_length=1, max_length=8000)
    thread_id: UUID | None = None
