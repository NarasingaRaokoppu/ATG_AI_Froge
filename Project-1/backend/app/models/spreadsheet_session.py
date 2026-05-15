"""Spreadsheet query session ORM model."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class SpreadsheetSession(Base):
    """Tracks uploaded spreadsheet context for follow-up questions."""

    __tablename__ = "spreadsheet_sessions"

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
    source_type: Mapped[str] = mapped_column(String(32), nullable=False)
    file_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    original_filename: Mapped[str | None] = mapped_column(String(512), nullable=True)
    mime_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    google_sheet_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    sheet_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    dataframe_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    thread: Mapped["Thread"] = relationship(back_populates="spreadsheet_sessions")  # noqa: F821
    user: Mapped["User"] = relationship(back_populates="spreadsheet_sessions")  # noqa: F821
    query_history: Mapped[list["SpreadsheetQueryHistory"]] = relationship(  # noqa: F821
        back_populates="spreadsheet_session",
        cascade="all, delete-orphan",
        order_by="SpreadsheetQueryHistory.created_at",
    )
