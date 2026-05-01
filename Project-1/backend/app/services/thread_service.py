"""Thread + message persistence services."""

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Message, Thread


async def create_thread(
    db: AsyncSession, user_id: UUID, title: str | None = None
) -> Thread:
    """Create a new thread for a user."""
    thread = Thread(user_id=user_id, title=title)
    db.add(thread)
    await db.commit()
    await db.refresh(thread)
    return thread


async def get_user_threads(db: AsyncSession, user_id: UUID) -> list[Thread]:
    """Return all threads for a user, newest first."""
    result = await db.scalars(
        select(Thread)
        .where(Thread.user_id == user_id)
        .order_by(Thread.created_at.desc())
    )
    return list(result)


async def get_thread_for_user(
    db: AsyncSession, thread_id: UUID, user_id: UUID
) -> Thread:
    """Fetch a thread, ensuring it belongs to the requesting user."""
    thread = await db.get(Thread, thread_id)
    if thread is None or thread.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "not_found", "message": "Thread not found"},
        )
    return thread


async def get_thread_messages(
    db: AsyncSession, thread_id: UUID, user_id: UUID
) -> list[Message]:
    """Return all messages for a thread the user owns."""
    await get_thread_for_user(db, thread_id, user_id)
    result = await db.scalars(
        select(Message)
        .where(Message.thread_id == thread_id)
        .order_by(Message.created_at.asc())
    )
    return list(result)


async def save_message(
    db: AsyncSession, *, thread_id: UUID, role: str, content: str
) -> Message:
    """Persist a single message."""
    message = Message(thread_id=thread_id, role=role, content=content)
    db.add(message)
    await db.commit()
    await db.refresh(message)
    return message


async def maybe_set_title(
    db: AsyncSession, thread: Thread, fallback_text: str
) -> None:
    """Auto-generate a thread title from the first message if missing."""
    if thread.title:
        return
    title = fallback_text.strip().splitlines()[0][:80]
    if not title:
        return
    thread.title = title
    db.add(thread)
    await db.commit()
