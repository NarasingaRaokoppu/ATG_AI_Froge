"""Message routes."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db import get_db
from app.models import User
from app.schemas.message import MessageResponse
from app.services import thread_service

router = APIRouter(prefix="/messages", tags=["messages"])


@router.get("/{thread_id}", response_model=list[MessageResponse])
async def list_messages(
    thread_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list:
    """Return all messages for a thread the user owns."""
    return await thread_service.get_thread_messages(db, thread_id, current_user.id)
