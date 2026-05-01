"""Message schemas."""

from datetime import datetime
from typing import Any
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

Role = Literal["user", "assistant"]
AttachmentType = Literal["image", "video", "table", "code", "formula"]


class MessageAttachment(BaseModel):
    """Attachment shape sent to frontend."""

    attachment_type: AttachmentType
    attachment_url: str | None = None
    content: str | None = None
    name: str | None = None
    mime_type: str | None = None
    metadata: dict[str, Any] | None = None


class MessageResponse(BaseModel):
    """Chat message shape returned to clients."""

    id: UUID
    thread_id: UUID
    role: Role
    content: str
    attachment_type: str | None = None
    attachment_url: str | None = None
    attachment_metadata: dict[str, Any] | None = None
    attachments: list[MessageAttachment] = Field(default_factory=list)
    created_at: datetime

    model_config = {"from_attributes": True}


    @staticmethod
    def from_orm_message(message) -> "MessageResponse":
        metadata = message.attachment_metadata or {}
        raw_attachments = metadata.get("attachments") or []
        attachments = [MessageAttachment.model_validate(a) for a in raw_attachments]
        if not attachments and message.attachment_type:
            attachments = [
                MessageAttachment(
                    attachment_type=message.attachment_type,
                    attachment_url=message.attachment_url,
                    metadata=metadata or None,
                )
            ]
        return MessageResponse(
            id=message.id,
            thread_id=message.thread_id,
            role=message.role,
            content=message.content,
            attachment_type=message.attachment_type,
            attachment_url=message.attachment_url,
            attachment_metadata=message.attachment_metadata,
            attachments=attachments,
            created_at=message.created_at,
        )
