"""Schemas for spreadsheet upload, connection, query, and history."""

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field


ChartType = Literal["bar", "line", "pie", "table"]


class SpreadsheetChart(BaseModel):
    chart_type: ChartType = "table"
    x_axis: str | None = None
    y_axis: str | None = None


class SpreadsheetSessionResponse(BaseModel):
    id: UUID
    thread_id: UUID
    source_type: str
    file_path: str | None = None
    original_filename: str | None = None
    mime_type: str | None = None
    google_sheet_url: str | None = None
    sheet_name: str | None = None
    dataframe_metadata: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SpreadsheetUploadResponse(BaseModel):
    session: SpreadsheetSessionResponse
    message: str


class GoogleSheetConnectRequest(BaseModel):
    thread_id: UUID
    google_sheet_url: str | None = None
    spreadsheet_id: str | None = None
    worksheet_title: str | None = None


class SpreadsheetQueryRequest(BaseModel):
    thread_id: UUID
    spreadsheet_session_id: UUID | None = None
    question: str = Field(..., min_length=1, max_length=8000)


class SpreadsheetQueryResponse(BaseModel):
    question: str
    answer: str
    explanation: str
    generated_code: str
    computed_result: Any | None = None
    rows: list[dict[str, Any]] = Field(default_factory=list)
    columns: list[str] = Field(default_factory=list)
    chart: SpreadsheetChart = Field(default_factory=SpreadsheetChart)
    execution_ms: int
    intermediate_steps: list[str] = Field(default_factory=list)


class SpreadsheetHistoryResponse(BaseModel):
    id: UUID
    thread_id: UUID
    spreadsheet_session_id: UUID | None
    question: str
    generated_code: str
    answer_summary: str
    execution_ms: int
    row_count: int
    columns: list[str] | None = None
    chart_metadata: dict[str, Any] | None = None
    created_at: datetime

    model_config = {"from_attributes": True}