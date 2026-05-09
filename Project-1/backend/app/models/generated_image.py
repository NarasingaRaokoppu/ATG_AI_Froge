"""Generated image ORM model."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class GeneratedImage(Base):
    """Stores image generation output and metadata."""

    __tablename__ = "generated_images"
    __table_args__ = (
        Index("ix_generated_images_user_created", "user_id", "created_at"),
        Index("ix_generated_images_thread_created", "thread_id", "created_at"),
        Index("ix_generated_images_status", "status"),
    )

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
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    enhanced_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_url: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="completed")
    generation_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    style: Mapped[str | None] = mapped_column(String(64), nullable=True)
    aspect_ratio: Mapped[str | None] = mapped_column(String(16), nullable=True)
    model_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    source_image_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("generated_images.id", ondelete="SET NULL"),
        nullable=True,
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    logs: Mapped[list["ImageGenerationLog"]] = relationship(  # noqa: F821
        back_populates="generated_image",
        cascade="all, delete-orphan",
        order_by="ImageGenerationLog.created_at",
    )
