"""Schema introspection service for external SQL connections."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.chains.sql_chain import sql_chain
from app.services import db_connection_service


async def get_schema_for_connection(
    db: AsyncSession,
    *,
    user_id: UUID,
    connection_id: UUID,
) -> str:
    """Load relational schema metadata for a user-owned connection."""
    connection = await db_connection_service.get_connection_for_user(
        db,
        connection_id=connection_id,
        user_id=user_id,
    )
    async_db_url = db_connection_service._build_async_db_url(connection)
    return await sql_chain.introspect_schema(async_db_url)
