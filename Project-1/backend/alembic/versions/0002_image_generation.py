"""image generation schema

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-09 00:00:00
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "generated_images",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "thread_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("threads.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("enhanced_prompt", sa.Text(), nullable=True),
        sa.Column("image_url", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("generation_time_ms", sa.Integer(), nullable=True),
        sa.Column("style", sa.String(length=64), nullable=True),
        sa.Column("aspect_ratio", sa.String(length=16), nullable=True),
        sa.Column("model_name", sa.String(length=128), nullable=True),
        sa.Column(
            "source_image_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("generated_images.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_generated_images_user_id", "generated_images", ["user_id"])
    op.create_index("ix_generated_images_thread_id", "generated_images", ["thread_id"])
    op.create_index(
        "ix_generated_images_user_created",
        "generated_images",
        ["user_id", "created_at"],
    )
    op.create_index(
        "ix_generated_images_thread_created",
        "generated_images",
        ["thread_id", "created_at"],
    )
    op.create_index("ix_generated_images_status", "generated_images", ["status"])

    op.create_table(
        "image_generation_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "generated_image_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("generated_images.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "thread_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("threads.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("safety_blocked", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("provider_latency_ms", sa.Integer(), nullable=True),
        sa.Column("error_code", sa.String(length=64), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("request_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("response_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_image_generation_logs_generated_image_id",
        "image_generation_logs",
        ["generated_image_id"],
    )
    op.create_index("ix_image_generation_logs_user_id", "image_generation_logs", ["user_id"])
    op.create_index("ix_image_generation_logs_thread_id", "image_generation_logs", ["thread_id"])
    op.create_index(
        "ix_image_logs_user_created",
        "image_generation_logs",
        ["user_id", "created_at"],
    )
    op.create_index(
        "ix_image_logs_thread_created",
        "image_generation_logs",
        ["thread_id", "created_at"],
    )
    op.create_index("ix_image_logs_status", "image_generation_logs", ["status"])


def downgrade() -> None:
    op.drop_index("ix_image_logs_status", table_name="image_generation_logs")
    op.drop_index("ix_image_logs_thread_created", table_name="image_generation_logs")
    op.drop_index("ix_image_logs_user_created", table_name="image_generation_logs")
    op.drop_index("ix_image_generation_logs_thread_id", table_name="image_generation_logs")
    op.drop_index("ix_image_generation_logs_user_id", table_name="image_generation_logs")
    op.drop_index(
        "ix_image_generation_logs_generated_image_id",
        table_name="image_generation_logs",
    )
    op.drop_table("image_generation_logs")

    op.drop_index("ix_generated_images_status", table_name="generated_images")
    op.drop_index("ix_generated_images_thread_created", table_name="generated_images")
    op.drop_index("ix_generated_images_user_created", table_name="generated_images")
    op.drop_index("ix_generated_images_thread_id", table_name="generated_images")
    op.drop_index("ix_generated_images_user_id", table_name="generated_images")
    op.drop_table("generated_images")
