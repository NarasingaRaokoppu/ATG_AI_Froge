"""Repository operations for generated images and image generation logs."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.generated_image import GeneratedImage
from app.models.image_generation_log import ImageGenerationLog


class ImageRepository:
    """Persistence layer for image generation entities."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_generated_image(self, image: GeneratedImage) -> GeneratedImage:
        self.db.add(image)
        await self.db.commit()
        await self.db.refresh(image)
        return image

    async def create_log(self, log: ImageGenerationLog) -> ImageGenerationLog:
        self.db.add(log)
        await self.db.commit()
        await self.db.refresh(log)
        return log

    async def list_thread_images_for_user(
        self,
        *,
        thread_id: UUID,
        user_id: UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> list[GeneratedImage]:
        result = await self.db.scalars(
            select(GeneratedImage)
            .where(
                GeneratedImage.thread_id == thread_id,
                GeneratedImage.user_id == user_id,
                GeneratedImage.status == "completed",
            )
            .order_by(GeneratedImage.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result)

    async def get_generated_image_for_user(
        self,
        *,
        image_id: UUID,
        user_id: UUID,
    ) -> GeneratedImage | None:
        result = await self.db.scalar(
            select(GeneratedImage).where(
                GeneratedImage.id == image_id,
                GeneratedImage.user_id == user_id,
            )
        )
        return result

    async def delete_generated_image(self, image: GeneratedImage) -> None:
        await self.db.delete(image)
        await self.db.commit()
