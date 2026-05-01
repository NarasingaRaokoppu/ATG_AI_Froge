"""Chat orchestration — invokes the LCEL chain and persists messages."""

from collections.abc import AsyncGenerator
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.chains.chat_chain import chat_chain
from app.core import settings
from app.models import User
from app.services import thread_service


async def stream_chat_response(
    db: AsyncSession,
    *,
    current_user: User,
    message: str,
    thread_id: UUID | None,
) -> AsyncGenerator[dict, None]:
    """Stream tokens, persisting both the user prompt and assistant reply.

    Yields events shaped as:
        {"event": "thread", "thread_id": "..."}
        {"event": "token", "data": "..."}
        {"event": "done"}
    """
    # 1. Resolve thread (create if needed)
    if thread_id is None:
        thread = await thread_service.create_thread(db, user_id=current_user.id)
    else:
        thread = await thread_service.get_thread_for_user(
            db, thread_id, current_user.id
        )

    # 2. Persist the user message + auto-title
    await thread_service.save_message(
        db, thread_id=thread.id, role="user", content=message
    )
    await thread_service.maybe_set_title(
        db, thread, fallback_text=message, user_email=current_user.email
    )

    yield {"event": "thread", "thread_id": str(thread.id)}

    # 3. Stream LLM tokens — every AI call carries user_email metadata
    config = {
        "metadata": {
            "user_email": current_user.email,
            "application": settings.APP_NAME,
            "environment": settings.ENVIRONMENT,
        }
    }

    chunks: list[str] = []
    async for token in chat_chain.astream({"message": message}, config=config):
        if not token:
            continue
        chunks.append(token)
        yield {"event": "token", "data": token}

    # 4. Persist the assembled assistant reply
    full_reply = "".join(chunks)
    if full_reply:
        await thread_service.save_message(
            db, thread_id=thread.id, role="assistant", content=full_reply
        )

    yield {"event": "done"}
