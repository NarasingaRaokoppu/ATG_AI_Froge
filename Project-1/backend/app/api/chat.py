"""Chat HTTP routes — thin wrappers that delegate to the service layer."""

import json
from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from openai import OpenAIError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db import get_db
from app.models import User
from app.schemas.chat import ChatRequest
from app.services import chat_service

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("")
async def chat(
    payload: ChatRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> StreamingResponse:
    """Stream a chat completion as Server-Sent Events.

    Each SSE frame carries a JSON object so the client can distinguish
    between thread metadata, tokens, and the terminal `done` marker.
    """

    async def event_stream() -> AsyncGenerator[bytes, None]:
        try:
            async for event in chat_service.stream_chat_response(
                db,
                current_user=current_user,
                message=payload.message,
                thread_id=payload.thread_id,
                attachments=payload.attachments,
            ):
                frame = json.dumps(event, ensure_ascii=False)
                yield f"data: {frame}\n\n".encode("utf-8")
        except HTTPException:
            raise
        except OpenAIError as e:
            err = json.dumps(
                {"event": "error", "error": "llm_error", "message": str(e)}
            )
            yield f"data: {err}\n\n".encode("utf-8")
        except Exception as e:  # noqa: BLE001
            err = json.dumps(
                {"event": "error", "error": "unexpected", "message": str(e)}
            )
            yield f"data: {err}\n\n".encode("utf-8")

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
