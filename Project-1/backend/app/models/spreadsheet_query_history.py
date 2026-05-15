"""Spreadsheet query history ORM model."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class SpreadsheetQueryHistory(Base):
    """Stores spreadsheet question/answer history for a thread."""

    __tablename__ = "spreadsheet_query_history"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    thread_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("threads.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    spreadsheet_session_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("spreadsheet_sessions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    question: Mapped[str] = mapped_column(Text, nullable=False)
    generated_code: Mapped[str] = mapped_column(Text, nullable=False)
    answer_summary: Mapped[str] = mapped_column(Text, nullable=False)
    execution_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    row_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    columns: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    chart_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    intermediate_steps: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="spreadsheet_query_history")  # noqa: F821
    thread: Mapped["Thread"] = relationship(back_populates="spreadsheet_query_history")  # noqa: F821
    spreadsheet_session: Mapped["SpreadsheetSession | None"] = relationship(  # noqa: F821
        back_populates="query_history"
    )
