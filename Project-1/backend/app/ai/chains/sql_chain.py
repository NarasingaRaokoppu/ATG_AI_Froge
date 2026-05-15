"""NL-to-SQL chain: schema introspection, SQL generation, execution, explanation."""

from __future__ import annotations

import asyncio
import json
import time
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Any

from langchain_community.utilities import SQLDatabase
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from sqlalchemy import create_engine, text

from app.ai.llm import llm

_PROMPT_DIR = Path(__file__).resolve().parent.parent / "prompts"
_SQL_GENERATION_PROMPT = (_PROMPT_DIR / "sql_generation_prompt.txt").read_text(
    encoding="utf-8"
)
_SQL_EXPLANATION_PROMPT = (_PROMPT_DIR / "sql_explanation_prompt.txt").read_text(
    encoding="utf-8"
)

_parser = StrOutputParser()

_sql_generation_chain = (
    ChatPromptTemplate.from_template(_SQL_GENERATION_PROMPT) | llm | _parser
)
_sql_explanation_chain = (
    ChatPromptTemplate.from_template(_SQL_EXPLANATION_PROMPT) | llm | _parser
)


def _sanitize_sql_from_llm(text_response: str) -> str:
    cleaned = text_response.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        cleaned = cleaned.replace("sql", "", 1).strip()
    return cleaned


def _to_json_safe(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, dict):
        return {k: _to_json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_to_json_safe(v) for v in value]
    return str(value)


def _build_sync_db_url(db_url: str) -> str:
    """Convert async SQLAlchemy URL to psycopg2 sync URL for SQLDatabase."""
    if db_url.startswith("postgresql+asyncpg://"):
        return db_url.replace("postgresql+asyncpg://", "postgresql+psycopg2://", 1)
    return db_url


def _execute_query_sync(sync_db_url: str, sql: str) -> tuple[list[dict[str, Any]], list[str], int]:
    engine = create_engine(sync_db_url, pool_pre_ping=True)
    started = time.perf_counter()
    try:
        with engine.connect() as conn:
            result = conn.execute(text(sql))
            rows = [dict(row) for row in result.mappings().all()]
            columns = list(result.keys())
    finally:
        engine.dispose()
    elapsed_ms = int((time.perf_counter() - started) * 1000)
    return [_to_json_safe(row) for row in rows], columns, elapsed_ms


class SqlChain:
    """Orchestrates schema introspection, SQL generation, execution and explanation."""

    @staticmethod
    def _build_sync_db_url(db_url: str) -> str:
        return _build_sync_db_url(db_url)

    async def introspect_schema(self, async_db_url: str) -> str:
        sync_db_url = _build_sync_db_url(async_db_url)

        def _read_schema() -> str:
            database = SQLDatabase.from_uri(sync_db_url)
            return database.get_table_info()

        return await asyncio.to_thread(_read_schema)

    async def generate_sql(
        self,
        *,
        question: str,
        schema_text: str,
        history_text: str,
        user_email: str,
    ) -> str:
        sql = await _sql_generation_chain.ainvoke(
            {
                "question": question,
                "schema": schema_text,
                "history": history_text,
            },
            config={"metadata": {"user_email": user_email}},
        )
        return _sanitize_sql_from_llm(str(sql))

    async def execute_sql(
        self,
        *,
        async_db_url: str,
        sql: str,
    ) -> tuple[list[dict[str, Any]], list[str], int]:
        sync_db_url = _build_sync_db_url(async_db_url)
        return await asyncio.to_thread(_execute_query_sync, sync_db_url, sql)

    async def explain(
        self,
        *,
        question: str,
        sql: str,
        rows: list[dict[str, Any]],
        user_email: str,
    ) -> str:
        preview = rows[:25]
        return await _sql_explanation_chain.ainvoke(
            {
                "question": question,
                "sql": sql,
                "rows_json": json.dumps(preview, ensure_ascii=False),
            },
            config={"metadata": {"user_email": user_email}},
        )

    async def stream_explanation(
        self,
        *,
        question: str,
        sql: str,
        rows: list[dict[str, Any]],
        user_email: str,
    ) -> AsyncGenerator[str, None]:
        preview = rows[:25]
        async for token in _sql_explanation_chain.astream(
            {
                "question": question,
                "sql": sql,
                "rows_json": json.dumps(preview, ensure_ascii=False),
            },
            config={"metadata": {"user_email": user_email}},
        ):
            if token:
                yield token


sql_chain = SqlChain()

__all__ = ["sql_chain", "_build_sync_db_url"]
