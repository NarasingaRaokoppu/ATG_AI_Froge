"""Thread schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ThreadCreate(BaseModel):
    """Optional title when creating a thread."""

    title: str | None = Field(default=None, max_length=255)


class ThreadUpdate(BaseModel):
    """Rename a thread."""

    title: str = Field(..., min_length=1, max_length=255)


class ThreadResponse(BaseModel):
    """Thread shape returned to clients."""

    id: UUID
    title: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
