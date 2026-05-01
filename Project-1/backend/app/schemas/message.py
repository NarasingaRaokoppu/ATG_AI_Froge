"""Message schemas."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel

Role = Literal["user", "assistant"]


class MessageResponse(BaseModel):
    """Chat message shape returned to clients."""

    id: UUID
    thread_id: UUID
    role: Role
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}
