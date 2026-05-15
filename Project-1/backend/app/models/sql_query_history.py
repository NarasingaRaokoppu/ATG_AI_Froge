"""SQL query history ORM model for NL-to-SQL interactions."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class SqlQueryHistory(Base):
    """Stores generated SQL metadata and outcomes for a thread."""

    __tablename__ = "sql_query_history"

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
    database_connection_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("database_connections.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    source_type: Mapped[str] = mapped_column(String(32), nullable=False, default="database")
    user_question: Mapped[str] = mapped_column(Text, nullable=False)
    generated_sql: Mapped[str] = mapped_column(Text, nullable=False)
    execution_time_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    row_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    result_columns: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    result_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    assistant_summary: Mapped[str] = mapped_column(Text, nullable=False)
    chart_suggestion: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    thread: Mapped["Thread"] = relationship(back_populates="sql_query_history")  # noqa: F821
    user: Mapped["User"] = relationship(back_populates="sql_query_history")  # noqa: F821
    database_connection: Mapped["DatabaseConnection | None"] = relationship()  # noqa: F821
