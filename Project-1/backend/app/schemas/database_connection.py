"""Schemas for saved database connections."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class DatabaseConnectionCreate(BaseModel):
    """Payload to create a database connection."""

    name: str = Field(..., min_length=1, max_length=128)
    host: str = Field(..., min_length=1, max_length=255)
    port: int = Field(default=5432, ge=1, le=65535)
    database: str = Field(..., min_length=1, max_length=255)
    username: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=1, max_length=2048)


class DatabaseConnectionUpdate(BaseModel):
    """Partial update payload for a database connection."""

    name: str | None = Field(default=None, min_length=1, max_length=128)
    host: str | None = Field(default=None, min_length=1, max_length=255)
    port: int | None = Field(default=None, ge=1, le=65535)
    database: str | None = Field(default=None, min_length=1, max_length=255)
    username: str | None = Field(default=None, min_length=1, max_length=255)
    password: str | None = Field(default=None, min_length=1, max_length=2048)


class DatabaseConnectionResponse(BaseModel):
    """Connection response shape without sensitive fields."""

    id: UUID
    name: str
    host: str
    port: int
    database: str
    username: str
    has_password: bool = True
    created_at: datetime
    updated_at: datetime
    last_tested_at: datetime | None

    model_config = {"from_attributes": True}


class ConnectionTestResponse(BaseModel):
    """Response payload for connection test endpoint."""

    success: bool
    message: str