"""Business logic for user-owned database connections."""

from __future__ import annotations

from datetime import datetime, timezone
from urllib.parse import quote_plus
from uuid import UUID

from cryptography.fernet import Fernet, InvalidToken
from fastapi import HTTPException, status
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.core import settings
from app.models import DatabaseConnection
from app.schemas.database_connection import (
    ConnectionTestResponse,
    DatabaseConnectionCreate,
    DatabaseConnectionUpdate,
)


def _get_fernet() -> Fernet:
    key = settings.DB_CONNECTION_ENCRYPTION_KEY
    if not key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "encryption_key_missing",
                "message": "DB_CONNECTION_ENCRYPTION_KEY is not configured.",
            },
        )
    try:
        return Fernet(key.encode("utf-8"))
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "encryption_key_invalid",
                "message": "DB_CONNECTION_ENCRYPTION_KEY is invalid.",
            },
        ) from exc


def encrypt_password(plaintext_password: str) -> str:
    """Encrypt a plaintext password with Fernet."""
    fernet = _get_fernet()
    return fernet.encrypt(plaintext_password.encode("utf-8")).decode("utf-8")


def decrypt_password(ciphertext: str) -> str:
    """Decrypt a stored Fernet-encrypted password."""
    fernet = _get_fernet()
    try:
        return fernet.decrypt(ciphertext.encode("utf-8")).decode("utf-8")
    except InvalidToken as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "password_decrypt_failed",
                "message": "Stored database password could not be decrypted.",
            },
        ) from exc


def _build_async_db_url(connection: DatabaseConnection) -> str:
    password = decrypt_password(connection.encrypted_password)
    encoded_username = quote_plus(connection.username)
    encoded_password = quote_plus(password)
    return (
        "postgresql+asyncpg://"
        f"{encoded_username}:{encoded_password}@{connection.host}:{connection.port}/{connection.database}"
    )


def _build_connect_args(connection: DatabaseConnection) -> dict:
    """Mirror provider-specific asyncpg connection options used by the app DB."""
    connect_args: dict = {}
    if "supabase" in connection.host:
        connect_args["ssl"] = "require"
        if connection.port == 6543:
            connect_args["statement_cache_size"] = 0
    return connect_args


async def create_connection(
    db: AsyncSession,
    *,
    user_id: UUID,
    payload: DatabaseConnectionCreate,
) -> DatabaseConnection:
    """Create a new saved database connection."""
    connection = DatabaseConnection(
        user_id=user_id,
        name=payload.name,
        host=payload.host,
        port=payload.port,
        database=payload.database,
        username=payload.username,
        encrypted_password=encrypt_password(payload.password),
    )
    db.add(connection)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "connection_name_conflict",
                "message": "A connection with this name already exists.",
            },
        ) from exc
    await db.refresh(connection)
    return connection


async def list_connections(db: AsyncSession, *, user_id: UUID) -> list[DatabaseConnection]:
    """Return all saved connections for a user."""
    result = await db.scalars(
        select(DatabaseConnection)
        .where(DatabaseConnection.user_id == user_id)
        .order_by(DatabaseConnection.created_at.desc())
    )
    return list(result)


async def get_connection_for_user(
    db: AsyncSession,
    *,
    connection_id: UUID,
    user_id: UUID,
) -> DatabaseConnection:
    """Fetch a connection and enforce ownership."""
    connection = await db.get(DatabaseConnection, connection_id)
    if connection is None or connection.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "not_found", "message": "Connection not found"},
        )
    return connection


async def update_connection(
    db: AsyncSession,
    *,
    connection_id: UUID,
    user_id: UUID,
    payload: DatabaseConnectionUpdate,
) -> DatabaseConnection:
    """Update a saved connection owned by a user."""
    connection = await get_connection_for_user(
        db,
        connection_id=connection_id,
        user_id=user_id,
    )

    updates = payload.model_dump(exclude_unset=True)
    if "password" in updates:
        connection.encrypted_password = encrypt_password(updates.pop("password"))

    for field, value in updates.items():
        setattr(connection, field, value)

    db.add(connection)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "connection_name_conflict",
                "message": "A connection with this name already exists.",
            },
        ) from exc
    await db.refresh(connection)
    return connection


async def delete_connection(
    db: AsyncSession,
    *,
    connection_id: UUID,
    user_id: UUID,
) -> None:
    """Delete a saved connection owned by a user."""
    connection = await get_connection_for_user(
        db,
        connection_id=connection_id,
        user_id=user_id,
    )
    await db.delete(connection)
    await db.commit()


async def test_connection(
    db: AsyncSession,
    *,
    connection_id: UUID,
    user_id: UUID,
) -> ConnectionTestResponse:
    """Test connectivity to a saved PostgreSQL connection."""
    connection = await get_connection_for_user(
        db,
        connection_id=connection_id,
        user_id=user_id,
    )

    test_engine = create_async_engine(
        _build_async_db_url(connection),
        pool_pre_ping=True,
        connect_args=_build_connect_args(connection),
    )
    try:
        async with test_engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception as exc:  # noqa: BLE001
        return ConnectionTestResponse(success=False, message=f"Connection failed: {exc}")
    finally:
        await test_engine.dispose()

    connection.last_tested_at = datetime.now(timezone.utc)
    db.add(connection)
    await db.commit()
    return ConnectionTestResponse(success=True, message="Connection successful")