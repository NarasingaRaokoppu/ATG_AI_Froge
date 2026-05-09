"""Pydantic schemas for image generation APIs."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

ImageStatus = Literal["pending", "completed", "failed", "deleted"]
ImageStyle = Literal[
    "photorealistic",
    "cinematic",
    "anime",
    "digital-art",
    "watercolor",
    "minimal",
    "none",
]
AspectRatio = Literal["1:1", "16:9", "9:16", "4:3", "3:4"]


class ImageGenerateRequest(BaseModel):
    """Payload to generate an image from text."""

    prompt: str = Field(..., min_length=3, max_length=2000)
    thread_id: UUID | None = None
    style: ImageStyle = "none"
    aspect_ratio: AspectRatio = "1:1"
    enhance_prompt: bool = True


class ImageRegenerateRequest(BaseModel):
    """Payload to regenerate an existing generated image."""

    image_id: UUID
    prompt_override: str | None = Field(default=None, max_length=2000)
    style: ImageStyle | None = None
    aspect_ratio: AspectRatio | None = None
    enhance_prompt: bool = True


class GeneratedImageResponse(BaseModel):
    """Generated image entity returned to clients."""

    id: UUID
    user_id: UUID
    thread_id: UUID
    prompt: str
    enhanced_prompt: str | None
    image_url: str
    status: ImageStatus
    generation_time_ms: int | None
    style: str | None
    aspect_ratio: str | None
    model_name: str | None
    source_image_id: UUID | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ImageGenerateResponse(BaseModel):
    """Generate endpoint response."""

    thread_id: UUID
    image: GeneratedImageResponse


class ImageDeleteResponse(BaseModel):
    """Delete endpoint response."""

    deleted: bool
    image_id: UUID
