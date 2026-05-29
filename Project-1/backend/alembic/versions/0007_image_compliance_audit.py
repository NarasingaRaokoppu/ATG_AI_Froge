"""image compliance audit

Revision ID: 0007
Revises: 0006
Create Date: 2026-05-29 09:30:00
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0007"
down_revision: Union[str, None] = "0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "image_compliance_audits",
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
            sa.ForeignKey("threads.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("rule_set_name", sa.String(length=255), nullable=False),
        sa.Column("rules", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("input_images", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("results", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("passed_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_image_compliance_audits_user_id",
        "image_compliance_audits",
        ["user_id"],
    )
    op.create_index(
        "ix_image_compliance_audits_thread_id",
        "image_compliance_audits",
        ["thread_id"],
    )
    op.create_index(
        "ix_image_compliance_audits_user_created",
        "image_compliance_audits",
        ["user_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_image_compliance_audits_user_created",
        table_name="image_compliance_audits",
    )
    op.drop_index(
        "ix_image_compliance_audits_thread_id",
        table_name="image_compliance_audits",
    )
    op.drop_index(
        "ix_image_compliance_audits_user_id",
        table_name="image_compliance_audits",
    )
    op.drop_table("image_compliance_audits")
