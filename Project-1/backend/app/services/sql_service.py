"""SQL query orchestration service for natural-language database questions."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.chains.sql_chain import sql_chain
from app.models import SqlQueryHistory, User
from app.schemas.sql import ChartSuggestion, SqlQueryRequest, SqlQueryResponse
from app.services import db_connection_service, schema_service, thread_service
from app.services.sql_validator import validate_and_normalize_sql


def _history_as_text(messages: list[Any]) -> str:
    if not messages:
        return "(no previous conversation)"
    return "\n".join(
        f"{'User' if m.role == 'user' else 'Assistant'}: {m.content}" for m in messages
    )


def _chart_suggestion(rows: list[dict[str, Any]], columns: list[str]) -> ChartSuggestion:
    if not rows or not columns:
        return ChartSuggestion(chart_type="table")

    if len(columns) >= 2:
        first = columns[0]
        second = columns[1]
        second_values = [r.get(second) for r in rows[:20]]
        if all(isinstance(v, (int, float)) for v in second_values if v is not None):
            return ChartSuggestion(chart_type="bar", x_axis=first, y_axis=second)

    return ChartSuggestion(chart_type="table")


async def _save_sql_history(
    db: AsyncSession,
    *,
    user_id: UUID,
    thread_id: UUID,
    database_connection_id: UUID | None,
    source_type: str,
    question: str,
    generated_sql: str,
    execution_time_ms: int,
    rows: list[dict[str, Any]],
    columns: list[str],
    explanation: str,
    chart: ChartSuggestion,
) -> SqlQueryHistory:
    row = SqlQueryHistory(
        user_id=user_id,
        thread_id=thread_id,
        database_connection_id=database_connection_id,
        source_type=source_type,
        user_question=question,
        generated_sql=generated_sql,
        execution_time_ms=execution_time_ms,
        row_count=len(rows),
        result_columns=columns,
        result_metadata={"preview_count": min(len(rows), 50)},
        assistant_summary=explanation,
        chart_suggestion=chart.model_dump(),
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


async def run_sql_query(
    db: AsyncSession,
    *,
    current_user: User,
    payload: SqlQueryRequest,
) -> SqlQueryResponse:
    """Run end-to-end NL-to-SQL query and persist query history."""
    await thread_service.get_thread_for_user(db, payload.thread_id, current_user.id)

    connection = await db_connection_service.get_connection_for_user(
        db,
        connection_id=payload.connection_id,
        user_id=current_user.id,
    )
    async_db_url = db_connection_service._build_async_db_url(connection)

    recent_messages = await thread_service.get_recent_thread_messages_for_context(
        db,
        thread_id=payload.thread_id,
        user_id=current_user.id,
        limit=5,
    )
    history_text = _history_as_text(recent_messages)

    schema_text = await schema_service.get_schema_for_connection(
        db,
        user_id=current_user.id,
        connection_id=payload.connection_id,
    )
    generated_sql = await sql_chain.generate_sql(
        question=payload.question,
        schema_text=schema_text,
        history_text=history_text,
        user_email=current_user.email,
    )
    safe_sql = validate_and_normalize_sql(generated_sql)

    rows, columns, execution_time_ms = await sql_chain.execute_sql(
        async_db_url=async_db_url,
        sql=safe_sql,
    )

    chart = _chart_suggestion(rows, columns)
    explanation = await sql_chain.explain(
        question=payload.question,
        sql=safe_sql,
        rows=rows,
        user_email=current_user.email,
    )

    await _save_sql_history(
        db,
        user_id=current_user.id,
        thread_id=payload.thread_id,
        database_connection_id=payload.connection_id,
        source_type="database",
        question=payload.question,
        generated_sql=safe_sql,
        execution_time_ms=execution_time_ms,
        rows=rows,
        columns=columns,
        explanation=explanation,
        chart=chart,
    )

    return SqlQueryResponse(
        generated_sql=safe_sql,
        rows=rows,
        explanation=explanation,
        chart_suggestion=chart,
        execution_time_ms=execution_time_ms,
    )


async def stream_sql_query(
    db: AsyncSession,
    *,
    current_user: User,
    payload: SqlQueryRequest,
) -> AsyncGenerator[dict[str, Any], None]:
    """Stream SQL execution lifecycle and explanation tokens as SSE events."""
    await thread_service.get_thread_for_user(db, payload.thread_id, current_user.id)
    connection = await db_connection_service.get_connection_for_user(
        db,
        connection_id=payload.connection_id,
        user_id=current_user.id,
    )
    async_db_url = db_connection_service._build_async_db_url(connection)

    yield {"event": "status", "data": "Reading schema"}
    schema_text = await schema_service.get_schema_for_connection(
        db,
        user_id=current_user.id,
        connection_id=payload.connection_id,
    )

    recent_messages = await thread_service.get_recent_thread_messages_for_context(
        db,
        thread_id=payload.thread_id,
        user_id=current_user.id,
        limit=5,
    )
    history_text = _history_as_text(recent_messages)

    yield {"event": "status", "data": "Generating SQL"}
    generated_sql = await sql_chain.generate_sql(
        question=payload.question,
        schema_text=schema_text,
        history_text=history_text,
        user_email=current_user.email,
    )
    safe_sql = validate_and_normalize_sql(generated_sql)
    yield {"event": "sql", "data": safe_sql}

    yield {"event": "status", "data": "Executing query"}
    rows, columns, execution_time_ms = await sql_chain.execute_sql(
        async_db_url=async_db_url,
        sql=safe_sql,
    )
    chart = _chart_suggestion(rows, columns)

    yield {"event": "status", "data": "Explaining results"}
    explanation_parts: list[str] = []
    async for token in sql_chain.stream_explanation(
        question=payload.question,
        sql=safe_sql,
        rows=rows,
        user_email=current_user.email,
    ):
        explanation_parts.append(token)
        yield {"event": "token", "data": token}

    explanation = "".join(explanation_parts).strip()

    await _save_sql_history(
        db,
        user_id=current_user.id,
        thread_id=payload.thread_id,
        database_connection_id=payload.connection_id,
        source_type="database",
        question=payload.question,
        generated_sql=safe_sql,
        execution_time_ms=execution_time_ms,
        rows=rows,
        columns=columns,
        explanation=explanation,
        chart=chart,
    )

    yield {
        "event": "done",
        "data": {
            "generated_sql": safe_sql,
            "rows": rows,
            "explanation": explanation,
            "chart_suggestion": chart.model_dump(),
            "execution_time_ms": execution_time_ms,
        },
    }


async def list_thread_history(
    db: AsyncSession,
    *,
    current_user: User,
    thread_id: UUID,
) -> list[SqlQueryHistory]:
    """Fetch SQL/spreadsheet query history for a thread owned by current user."""
    await thread_service.get_thread_for_user(db, thread_id, current_user.id)
    result = await db.scalars(
        select(SqlQueryHistory)
        .where(
            SqlQueryHistory.user_id == current_user.id,
            SqlQueryHistory.thread_id == thread_id,
        )
        .order_by(SqlQueryHistory.created_at.desc())
    )
    return list(result)
