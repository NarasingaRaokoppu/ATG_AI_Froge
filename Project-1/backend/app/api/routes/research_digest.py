"""Research digest routes for Project 10."""

import json
from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from app.core.security import get_current_user
from app.models import User
from app.schemas.research_digest import ResearchDigestRequest
from app.services import research_digest_service

router = APIRouter(prefix="/research-digest", tags=["research-digest"])


@router.post("/stream")
async def stream_digest(
    payload: ResearchDigestRequest,
    _: Annotated[User, Depends(get_current_user)],
) -> StreamingResponse:
    """Run the research digest agent and stream SSE events."""

    async def event_stream() -> AsyncGenerator[bytes, None]:
        try:
            async for event in research_digest_service.stream_research_digest(payload):
                frame = json.dumps(event, ensure_ascii=False)
                yield f"data: {frame}\n\n".encode("utf-8")
        except HTTPException as exc:
            detail = exc.detail if isinstance(exc.detail, dict) else {"message": str(exc.detail)}
            frame = json.dumps(
                {
                    "event": "error",
                    "error": detail.get("error", "http_error"),
                    "message": detail.get("message", "Request failed"),
                },
                ensure_ascii=False,
            )
            yield f"data: {frame}\n\n".encode("utf-8")
        except Exception as exc:  # noqa: BLE001
            frame = json.dumps(
                {
                    "event": "error",
                    "error": "unexpected",
                    "message": str(exc),
                },
                ensure_ascii=False,
            )
            yield f"data: {frame}\n\n".encode("utf-8")

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
