"""Pydantic schemas for chat endpoints."""

from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field


AttachmentType = Literal["image", "video", "video_frame", "table", "code", "formula", "excel", "docx", "txt"]


class ChatAttachment(BaseModel):
    """Attachment metadata sent with a chat message."""

    attachment_type: AttachmentType
    attachment_url: str | None = None
    content: str | None = None
    name: str | None = None
    mime_type: str | None = None
    metadata: dict[str, Any] | None = None


class ChatRequest(BaseModel):
    """Incoming chat message payload."""

    message: str = Field(..., min_length=1, max_length=8000)
    thread_id: UUID | None = None
    attachments: list[ChatAttachment] = Field(default_factory=list)
