"""Versioned image generation routes."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies.rate_limit import enforce_image_generation_rate_limit
from app.core import settings
from app.core.security import get_current_user
from app.db import get_db
from app.models import User
from app.schemas.image import (
    GeneratedImageResponse,
    ImageDeleteResponse,
    ImageGenerateRequest,
    ImageGenerateResponse,
    ImageRegenerateRequest,
)
from app.services.images.image_service import ImageService

router = APIRouter(prefix="/v1", tags=["images"])


@router.post(
    "/images/generate",
    response_model=ImageGenerateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def generate_image(
    payload: ImageGenerateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ImageGenerateResponse:
    """Generate an image from text prompt."""
    await enforce_image_generation_rate_limit(
        current_user.id,
        max_requests=settings.IMAGE_GEN_RATE_LIMIT_PER_MINUTE,
        per_seconds=60,
    )
    service = ImageService(db)
    image = await service.generate(payload=payload, current_user=current_user)
    return ImageGenerateResponse(thread_id=image.thread_id, image=image)


@router.get(
    "/threads/{thread_id}/images",
    response_model=list[GeneratedImageResponse],
)
async def list_thread_images(
    thread_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[GeneratedImageResponse]:
    """List generated images for a thread, newest first."""
    service = ImageService(db)
    return await service.list_thread_images(
        thread_id=thread_id,
        current_user=current_user,
        limit=limit,
        offset=offset,
    )


@router.delete(
    "/images/{image_id}",
    response_model=ImageDeleteResponse,
)
async def delete_image(
    image_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ImageDeleteResponse:
    """Delete generated image and remove underlying stored file."""
    service = ImageService(db)
    await service.delete_image(image_id=image_id, current_user=current_user)
    return ImageDeleteResponse(deleted=True, image_id=image_id)


@router.post(
    "/images/regenerate",
    response_model=ImageGenerateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def regenerate_image(
    payload: ImageRegenerateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ImageGenerateResponse:
    """Generate a variant from an existing image generation record."""
    await enforce_image_generation_rate_limit(
        current_user.id,
        max_requests=settings.IMAGE_GEN_RATE_LIMIT_PER_MINUTE,
        per_seconds=60,
    )
    service = ImageService(db)
    image = await service.regenerate(payload=payload, current_user=current_user)
    return ImageGenerateResponse(thread_id=image.thread_id, image=image)
