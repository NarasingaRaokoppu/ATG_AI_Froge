"""User ORM model."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class User(Base):
    """A user account."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(
        String(320), unique=True, index=True, nullable=False
    )
    hashed_password: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    threads: Mapped[list["Thread"]] = relationship(  # noqa: F821
        back_populates="user", cascade="all, delete-orphan"
    )
    database_connections: Mapped[list["DatabaseConnection"]] = relationship(  # noqa: F821
        back_populates="user",
        cascade="all, delete-orphan"
    )
    sql_query_history: Mapped[list["SqlQueryHistory"]] = relationship(  # noqa: F821
        cascade="all, delete-orphan"
    )
    spreadsheet_sessions: Mapped[list["SpreadsheetSession"]] = relationship(  # noqa: F821
        cascade="all, delete-orphan"
    )
    spreadsheet_query_history: Mapped[list["SpreadsheetQueryHistory"]] = relationship(  # noqa: F821
        back_populates="user",
        cascade="all, delete-orphan"
    )
