"""Spreadsheet upload, connect, query, and history routes."""

import json
from collections.abc import AsyncGenerator
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db import get_db
from app.models import User
from app.schemas.spreadsheet import (
    GoogleSheetConnectRequest,
    SpreadsheetHistoryResponse,
    SpreadsheetQueryRequest,
    SpreadsheetQueryResponse,
    SpreadsheetUploadResponse,
)
from app.services import spreadsheet_service

router = APIRouter(prefix="/spreadsheet", tags=["spreadsheet"])


@router.post("/upload", response_model=SpreadsheetUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_spreadsheet(
    thread_id: UUID = Form(...),
    file: UploadFile = File(...),
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> SpreadsheetUploadResponse:
    return await spreadsheet_service.upload_spreadsheet(
        db,
        current_user=current_user,
        thread_id=thread_id,
        file=file,
    )


@router.post("/google-sheet", response_model=SpreadsheetUploadResponse, status_code=status.HTTP_201_CREATED)
async def connect_google_sheet(
    payload: GoogleSheetConnectRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SpreadsheetUploadResponse:
    return await spreadsheet_service.connect_google_sheet(
        db,
        current_user=current_user,
        payload=payload,
    )


@router.post("/query", response_model=SpreadsheetQueryResponse)
async def query_spreadsheet(
    payload: SpreadsheetQueryRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> StreamingResponse:
    async def event_stream() -> AsyncGenerator[bytes, None]:
        try:
            async for event in spreadsheet_service.stream_spreadsheet_query(
                db,
                current_user=current_user,
                payload=payload,
            ):
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


@router.get("/history/{thread_id}", response_model=list[SpreadsheetHistoryResponse])
async def spreadsheet_history(
    thread_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[SpreadsheetHistoryResponse]:
    return await spreadsheet_service.list_spreadsheet_history(
        db,
        current_user=current_user,
        thread_id=thread_id,
    )