"""Spreadsheet upload, loading, querying, and history services."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Any
from uuid import UUID

import pandas as pd
from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.chains.pandas_chain import pandas_chain
from app.core import settings
from app.models import SpreadsheetQueryHistory, SpreadsheetSession, User
from app.schemas.spreadsheet import (
    GoogleSheetConnectRequest,
    SpreadsheetChart,
    SpreadsheetQueryRequest,
    SpreadsheetSessionResponse,
    SpreadsheetUploadResponse,
)
from app.services import thread_service
from app.services.google_sheet_service import load_google_sheet_dataframe

_ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls"}
_ALLOWED_MIME_TYPES = {
    "text/csv",
    "application/csv",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}


def _spreadsheet_dir() -> Path:
    base = Path(settings.UPLOAD_DIR)
    if not base.is_absolute():
        base = (Path(__file__).resolve().parents[2] / base).resolve()
    path = base / "spreadsheets"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _chart_suggestion(rows: list[dict[str, Any]], columns: list[str]) -> SpreadsheetChart:
    if not rows or len(columns) < 2:
        return SpreadsheetChart(chart_type="table")
    x_axis, y_axis = columns[0], columns[1]
    values = [row.get(y_axis) for row in rows[:20]]
    if all(isinstance(value, (int, float)) for value in values if value is not None):
        return SpreadsheetChart(chart_type="bar", x_axis=x_axis, y_axis=y_axis)
    return SpreadsheetChart(chart_type="table")


def _dataframe_metadata(dataframe: pd.DataFrame) -> dict[str, Any]:
    return {
        "rows": int(len(dataframe.index)),
        "columns": list(dataframe.columns),
        "dtypes": {key: str(value) for key, value in dataframe.dtypes.items()},
        "preview": dataframe.head(5).fillna("").to_dict(orient="records"),
    }


def _load_dataframe_from_path(path: Path) -> pd.DataFrame:
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path)
    return pd.read_excel(path)


async def _get_session_for_user(
    db: AsyncSession,
    *,
    session_id: UUID,
    user_id: UUID,
) -> SpreadsheetSession:
    session = await db.get(SpreadsheetSession, session_id)
    if session is None or session.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "not_found", "message": "Spreadsheet session not found"},
        )
    return session


async def upload_spreadsheet(
    db: AsyncSession,
    *,
    current_user: User,
    thread_id: UUID,
    file: UploadFile,
) -> SpreadsheetUploadResponse:
    await thread_service.get_thread_for_user(db, thread_id, current_user.id)
    filename = file.filename or "spreadsheet.csv"
    extension = Path(filename).suffix.lower()
    mime_type = (file.content_type or "application/octet-stream").lower()

    if extension not in _ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "unsupported_extension", "message": "Only .csv, .xlsx, and .xls files are supported"},
        )
    if mime_type not in _ALLOWED_MIME_TYPES and mime_type != "application/octet-stream":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "unsupported_mime_type", "message": f"Unsupported spreadsheet MIME type: {mime_type}"},
        )

    max_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024
    content = await file.read()
    await file.close()
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail={"error": "file_too_large", "message": f"File exceeds {settings.MAX_UPLOAD_MB} MB limit"},
        )

    folder = _spreadsheet_dir() / str(current_user.id) / str(thread_id)
    folder.mkdir(parents=True, exist_ok=True)
    stored_path = folder / filename
    stored_path.write_bytes(content)

    dataframe = _load_dataframe_from_path(stored_path)
    session = SpreadsheetSession(
        user_id=current_user.id,
        thread_id=thread_id,
        source_type="csv" if extension == ".csv" else "excel",
        file_path=str(stored_path),
        original_filename=filename,
        mime_type=mime_type,
        dataframe_metadata=_dataframe_metadata(dataframe),
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)

    return SpreadsheetUploadResponse(
        session=SpreadsheetSessionResponse.model_validate(session),
        message="Spreadsheet uploaded successfully",
    )


async def connect_google_sheet(
    db: AsyncSession,
    *,
    current_user: User,
    payload: GoogleSheetConnectRequest,
) -> SpreadsheetUploadResponse:
    await thread_service.get_thread_for_user(db, payload.thread_id, current_user.id)
    dataframe, url, worksheet_title = load_google_sheet_dataframe(
        url=payload.google_sheet_url,
        spreadsheet_id=payload.spreadsheet_id,
        worksheet_title=payload.worksheet_title,
    )
    session = SpreadsheetSession(
        user_id=current_user.id,
        thread_id=payload.thread_id,
        source_type="google_sheets",
        google_sheet_url=url,
        sheet_name=worksheet_title,
        dataframe_metadata=_dataframe_metadata(dataframe),
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return SpreadsheetUploadResponse(
        session=SpreadsheetSessionResponse.model_validate(session),
        message="Google Sheet connected successfully",
    )


def _load_dataframe_for_session(session: SpreadsheetSession) -> pd.DataFrame:
    if session.source_type == "google_sheets":
        dataframe, _, _ = load_google_sheet_dataframe(
            url=session.google_sheet_url,
            spreadsheet_id=None,
            worksheet_title=session.sheet_name,
        )
        return dataframe
    if not session.file_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "missing_file_path", "message": "Spreadsheet file path is missing"},
        )
    path = Path(session.file_path)
    if not path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "file_not_found", "message": "Spreadsheet file not found on disk"},
        )
    return _load_dataframe_from_path(path)


async def _save_history(
    db: AsyncSession,
    *,
    current_user: User,
    thread_id: UUID,
    session_id: UUID,
    question: str,
    generated_code: str,
    answer_summary: str,
    execution_ms: int,
    columns: list[str],
    rows: list[dict[str, Any]],
    chart: SpreadsheetChart,
    intermediate_steps: list[str],
) -> SpreadsheetQueryHistory:
    entry = SpreadsheetQueryHistory(
        user_id=current_user.id,
        thread_id=thread_id,
        spreadsheet_session_id=session_id,
        question=question,
        generated_code=generated_code,
        answer_summary=answer_summary,
        execution_ms=execution_ms,
        row_count=len(rows),
        columns=columns,
        chart_metadata=chart.model_dump(),
        intermediate_steps=intermediate_steps,
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return entry


async def stream_spreadsheet_query(
    db: AsyncSession,
    *,
    current_user: User,
    payload: SpreadsheetQueryRequest,
) -> AsyncGenerator[dict[str, Any], None]:
    await thread_service.get_thread_for_user(db, payload.thread_id, current_user.id)
    if not payload.spreadsheet_session_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "missing_spreadsheet_session", "message": "spreadsheet_session_id is required"},
        )
    session = await _get_session_for_user(
        db,
        session_id=payload.spreadsheet_session_id,
        user_id=current_user.id,
    )
    dataframe = _load_dataframe_for_session(session)

    recent_messages = await thread_service.get_recent_thread_messages_for_context(
        db,
        thread_id=payload.thread_id,
        user_id=current_user.id,
        limit=5,
    )
    history_text = "\n".join(
        f"{'User' if item.role == 'user' else 'Assistant'}: {item.content}" for item in recent_messages
    ) or "(no previous conversation)"

    yield {"event": "status", "data": "Analyzing dataframe"}
    result = await pandas_chain.run_query(
        dataframe=dataframe,
        question=payload.question,
        history_text=history_text,
        user_email=current_user.email,
    )

    rows = result["rows"]
    columns = result["columns"]
    chart = _chart_suggestion(rows, columns)

    yield {"event": "code", "data": result["generated_code"]}
    yield {"event": "status", "data": "Generating answer"}

    answer_parts: list[str] = []
    async for token in pandas_chain.stream_answer(
        question=payload.question,
        rows=rows,
        user_email=current_user.email,
    ):
        answer_parts.append(token)
        yield {"event": "token", "data": token}

    answer = "".join(answer_parts).strip() or str(result["answer"])

    await _save_history(
        db,
        current_user=current_user,
        thread_id=payload.thread_id,
        session_id=session.id,
        question=payload.question,
        generated_code=result["generated_code"],
        answer_summary=answer,
        execution_ms=result["execution_ms"],
        columns=columns,
        rows=rows,
        chart=chart,
        intermediate_steps=result["intermediate_steps"],
    )

    yield {
        "event": "done",
        "data": {
            "question": payload.question,
            "answer": answer,
            "explanation": result["explanation"],
            "generated_code": result["generated_code"],
            "computed_result": result["computed_result"],
            "rows": rows,
            "columns": columns,
            "chart": chart.model_dump(),
            "execution_ms": result["execution_ms"],
            "intermediate_steps": result["intermediate_steps"],
        },
    }


async def list_spreadsheet_history(
    db: AsyncSession,
    *,
    current_user: User,
    thread_id: UUID,
) -> list[SpreadsheetQueryHistory]:
    await thread_service.get_thread_for_user(db, thread_id, current_user.id)
    result = await db.scalars(
        select(SpreadsheetQueryHistory)
        .where(
            SpreadsheetQueryHistory.user_id == current_user.id,
            SpreadsheetQueryHistory.thread_id == thread_id,
        )
        .order_by(SpreadsheetQueryHistory.created_at.desc())
    )
    return list(result)
