"""sql history and spreadsheet sessions

Revision ID: 0005
Revises: 0004
Create Date: 2026-05-15 00:20:00
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "sql_query_history",
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
            "database_connection_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("database_connections.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("source_type", sa.String(length=32), nullable=False),
        sa.Column("user_question", sa.Text(), nullable=False),
        sa.Column("generated_sql", sa.Text(), nullable=False),
        sa.Column("execution_time_ms", sa.Integer(), nullable=False),
        sa.Column("row_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("result_columns", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("result_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("assistant_summary", sa.Text(), nullable=False),
        sa.Column("chart_suggestion", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_sql_query_history_user_id", "sql_query_history", ["user_id"])
    op.create_index("ix_sql_query_history_thread_id", "sql_query_history", ["thread_id"])
    op.create_index(
        "ix_sql_query_history_db_connection_id",
        "sql_query_history",
        ["database_connection_id"],
    )
    op.create_index(
        "ix_sql_query_history_thread_created",
        "sql_query_history",
        ["thread_id", "created_at"],
    )

    op.create_table(
        "spreadsheet_sessions",
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
        sa.Column("source_type", sa.String(length=32), nullable=False),
        sa.Column("file_path", sa.Text(), nullable=True),
        sa.Column("original_filename", sa.String(length=512), nullable=True),
        sa.Column("mime_type", sa.String(length=128), nullable=True),
        sa.Column("google_sheet_url", sa.Text(), nullable=True),
        sa.Column("sheet_name", sa.String(length=255), nullable=True),
        sa.Column("dataframe_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_spreadsheet_sessions_user_id", "spreadsheet_sessions", ["user_id"])
    op.create_index("ix_spreadsheet_sessions_thread_id", "spreadsheet_sessions", ["thread_id"])
    op.create_index(
        "ix_spreadsheet_sessions_thread_created",
        "spreadsheet_sessions",
        ["thread_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_spreadsheet_sessions_thread_created", table_name="spreadsheet_sessions")
    op.drop_index("ix_spreadsheet_sessions_thread_id", table_name="spreadsheet_sessions")
    op.drop_index("ix_spreadsheet_sessions_user_id", table_name="spreadsheet_sessions")
    op.drop_table("spreadsheet_sessions")

    op.drop_index("ix_sql_query_history_thread_created", table_name="sql_query_history")
    op.drop_index("ix_sql_query_history_db_connection_id", table_name="sql_query_history")
    op.drop_index("ix_sql_query_history_thread_id", table_name="sql_query_history")
    op.drop_index("ix_sql_query_history_user_id", table_name="sql_query_history")
    op.drop_table("sql_query_history")
