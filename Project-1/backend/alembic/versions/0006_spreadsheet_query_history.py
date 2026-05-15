"""spreadsheet query history

Revision ID: 0006
Revises: 0005
Create Date: 2026-05-15 01:30:00
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "spreadsheet_query_history",
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
        sa.Column(
            "spreadsheet_session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("spreadsheet_sessions.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("generated_code", sa.Text(), nullable=False),
        sa.Column("answer_summary", sa.Text(), nullable=False),
        sa.Column("execution_ms", sa.Integer(), nullable=False),
        sa.Column("row_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("columns", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("chart_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("intermediate_steps", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_spreadsheet_query_history_user_id", "spreadsheet_query_history", ["user_id"])
    op.create_index("ix_spreadsheet_query_history_thread_id", "spreadsheet_query_history", ["thread_id"])
    op.create_index(
        "ix_spreadsheet_query_history_session_id",
        "spreadsheet_query_history",
        ["spreadsheet_session_id"],
    )
    op.create_index(
        "ix_spreadsheet_query_history_thread_created",
        "spreadsheet_query_history",
        ["thread_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_spreadsheet_query_history_thread_created", table_name="spreadsheet_query_history")
    op.drop_index("ix_spreadsheet_query_history_session_id", table_name="spreadsheet_query_history")
    op.drop_index("ix_spreadsheet_query_history_thread_id", table_name="spreadsheet_query_history")
    op.drop_index("ix_spreadsheet_query_history_user_id", table_name="spreadsheet_query_history")
    op.drop_table("spreadsheet_query_history")
