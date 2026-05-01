"""Thread routes."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db import get_db
from app.models import User
from app.schemas.thread import ThreadCreate, ThreadResponse
from app.services import thread_service

router = APIRouter(prefix="/threads", tags=["threads"])


@router.get("", response_model=list[ThreadResponse])
async def list_threads(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list:
    """Return all threads owned by the current user."""
    return await thread_service.get_user_threads(db, current_user.id)


@router.post(
    "",
    response_model=ThreadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_thread(
    payload: ThreadCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Create a new empty thread."""
    return await thread_service.create_thread(
        db, user_id=current_user.id, title=payload.title
    )


@router.delete("/{thread_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_thread(
    thread_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Delete a thread (and its messages)."""
    thread = await thread_service.get_thread_for_user(db, thread_id, current_user.id)
    await db.delete(thread)
    await db.commit()
