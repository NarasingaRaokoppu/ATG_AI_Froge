"""Schemas for SQL and spreadsheet natural-language querying."""

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field


ChartType = Literal["bar", "line", "pie", "table"]


class ChartSuggestion(BaseModel):
    """Chart recommendation for frontend visualization."""

    chart_type: ChartType = "table"
    x_axis: str | None = None
    y_axis: str | None = None


class SqlQueryRequest(BaseModel):
    """Incoming natural language query against a database connection."""

    thread_id: UUID
    connection_id: UUID
    question: str = Field(..., min_length=1, max_length=8000)


class SpreadsheetQueryRequest(BaseModel):
    """Incoming natural language query against spreadsheet sources."""

    thread_id: UUID
    question: str = Field(..., min_length=1, max_length=8000)
    spreadsheet_session_id: UUID | None = None
    google_sheet_url: str | None = None
    file_path: str | None = None


class SqlQueryResponse(BaseModel):
    """Structured result of generated SQL execution."""

    generated_sql: str
    rows: list[dict[str, Any]] = Field(default_factory=list)
    explanation: str
    chart_suggestion: ChartSuggestion = Field(default_factory=ChartSuggestion)
    execution_time_ms: int


class SpreadsheetQueryResponse(BaseModel):
    """Structured result of generated pandas execution."""

    generated_code: str
    rows: list[dict[str, Any]] = Field(default_factory=list)
    explanation: str
    chart_suggestion: ChartSuggestion = Field(default_factory=ChartSuggestion)


class SqlQueryHistoryResponse(BaseModel):
    """History entry shape returned by history endpoint."""

    id: UUID
    thread_id: UUID
    database_connection_id: UUID | None
    source_type: str
    user_question: str
    generated_sql: str
    execution_time_ms: int
    row_count: int
    result_columns: list[str] | None = None
    assistant_summary: str
    chart_suggestion: dict[str, Any] | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
