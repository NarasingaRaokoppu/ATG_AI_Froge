"""SQL/Data Explorer routes for database connection management."""

import json
from collections.abc import AsyncGenerator
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db import get_db
from app.models import User
from app.schemas.database_connection import (
    ConnectionTestResponse,
    DatabaseConnectionCreate,
    DatabaseConnectionResponse,
    DatabaseConnectionUpdate,
)
from app.schemas.sql import (
    SpreadsheetQueryRequest,
    SpreadsheetQueryResponse,
    SqlQueryHistoryResponse,
    SqlQueryRequest,
    SqlQueryResponse,
)
from app.services import db_connection_service, spreadsheet_service, sql_service

router = APIRouter(tags=["sql"])


@router.post(
    "/connections",
    response_model=DatabaseConnectionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_connection(
    payload: DatabaseConnectionCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DatabaseConnectionResponse:
    """Create a saved external database connection for the current user."""
    return await db_connection_service.create_connection(
        db,
        user_id=current_user.id,
        payload=payload,
    )


@router.get("/connections", response_model=list[DatabaseConnectionResponse])
async def list_connections(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[DatabaseConnectionResponse]:
    """List all saved database connections for the current user."""
    return await db_connection_service.list_connections(db, user_id=current_user.id)


@router.patch("/connections/{connection_id}", response_model=DatabaseConnectionResponse)
async def update_connection(
    connection_id: UUID,
    payload: DatabaseConnectionUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DatabaseConnectionResponse:
    """Update a saved database connection."""
    return await db_connection_service.update_connection(
        db,
        connection_id=connection_id,
        user_id=current_user.id,
        payload=payload,
    )


@router.delete("/connections/{connection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_connection(
    connection_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Delete a saved database connection."""
    await db_connection_service.delete_connection(
        db,
        connection_id=connection_id,
        user_id=current_user.id,
    )


@router.post(
    "/connections/{connection_id}/test",
    response_model=ConnectionTestResponse,
)
async def test_connection(
    connection_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ConnectionTestResponse:
    """Test connectivity for a saved database connection."""
    return await db_connection_service.test_connection(
        db,
        connection_id=connection_id,
        user_id=current_user.id,
    )


@router.post("/query", response_model=SqlQueryResponse)
async def query_database(
    payload: SqlQueryRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> StreamingResponse:
    """Stream natural-language SQL query execution as SSE events."""

    async def event_stream() -> AsyncGenerator[bytes, None]:
        try:
            async for event in sql_service.stream_sql_query(
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


@router.post("/spreadsheet/query", response_model=SpreadsheetQueryResponse)
async def query_spreadsheet(
    payload: SpreadsheetQueryRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SpreadsheetQueryResponse:
    """Run natural-language query over spreadsheet sources."""
    return await spreadsheet_service.query_spreadsheet(
        db,
        current_user=current_user,
        payload=payload,
    )


@router.get("/history/{thread_id}", response_model=list[SqlQueryHistoryResponse])
async def get_query_history(
    thread_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[SqlQueryHistoryResponse]:
    """Return SQL and spreadsheet query history for a thread."""
    return await sql_service.list_thread_history(
        db,
        current_user=current_user,
        thread_id=thread_id,
    )