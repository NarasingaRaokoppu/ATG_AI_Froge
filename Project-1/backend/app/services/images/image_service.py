"""Image generation domain service."""

from __future__ import annotations

import hashlib
import re
import time
import uuid
from pathlib import Path
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import settings
from app.db.repositories.image_repository import ImageRepository
from app.models.generated_image import GeneratedImage
from app.models.image_generation_log import ImageGenerationLog
from app.models.user import User
from app.schemas.image import ImageGenerateRequest, ImageRegenerateRequest
from app.services import thread_service
from app.services.ai.gemini_image_client import GeminiImageClient, GeminiImageClientError

_BLOCKED_TERMS = {
    "child sexual",
    "terrorist manifesto",
    "explosive instruction",
    "self harm tutorial",
    "extremist propaganda",
}

_STYLE_HINTS = {
    "photorealistic": "ultra detailed, realistic lighting, DSLR quality",
    "cinematic": "cinematic composition, dramatic lighting, film still",
    "anime": "anime style, cel shaded, clean line art",
    "digital-art": "digital illustration, concept art, rich details",
    "watercolor": "watercolor brush texture, artistic paper grain",
    "minimal": "minimalist composition, clean visual hierarchy",
    "none": "",
}


class ImageService:
    """Orchestrates AI generation, persistence, and audit logs."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = ImageRepository(db)
        self.ai_client = GeminiImageClient()

    async def generate(
        self,
        *,
        payload: ImageGenerateRequest,
        current_user: User,
    ) -> GeneratedImage:
        thread = await self._resolve_thread(payload.thread_id, current_user)
        safe_prompt = self._sanitize_prompt(payload.prompt)
        enhanced_prompt = self._enhance_prompt(
            prompt=safe_prompt,
            style=payload.style,
            aspect_ratio=payload.aspect_ratio,
            enabled=payload.enhance_prompt,
        )

        self._validate_prompt_safety(enhanced_prompt)

        started = time.perf_counter()
        provider_response: dict | None = None
        image: GeneratedImage | None = None

        try:
            ai_result = await self.ai_client.generate_image(
                prompt=enhanced_prompt,
                aspect_ratio=payload.aspect_ratio,
                user_email=current_user.email,
            )
            provider_response = ai_result.raw_response
            file_url = self._persist_generated_image(
                image_bytes=ai_result.image_bytes,
                mime_type=ai_result.mime_type,
            )

            generation_ms = int((time.perf_counter() - started) * 1000)
            image = await self.repo.create_generated_image(
                GeneratedImage(
                    user_id=current_user.id,
                    thread_id=thread.id,
                    prompt=safe_prompt,
                    enhanced_prompt=enhanced_prompt,
                    image_url=file_url,
                    status="completed",
                    generation_time_ms=generation_ms,
                    style=payload.style,
                    aspect_ratio=payload.aspect_ratio,
                    model_name=settings.IMAGE_GEN_MODEL,
                )
            )

            await thread_service.save_message(
                self.db,
                thread_id=thread.id,
                role="assistant",
                content=f"Generated image for prompt: {safe_prompt}",
                attachment_type="image",
                attachment_url=file_url,
                attachment_metadata={
                    "generated_image_id": str(image.id),
                    "style": payload.style,
                    "aspect_ratio": payload.aspect_ratio,
                },
            )

            await self._write_log(
                generated_image_id=image.id,
                user_id=current_user.id,
                thread_id=thread.id,
                status="completed",
                event_type="generate",
                safety_blocked=False,
                provider_latency_ms=generation_ms,
                request_payload={
                    "prompt": safe_prompt,
                    "enhanced_prompt": enhanced_prompt,
                    "style": payload.style,
                    "aspect_ratio": payload.aspect_ratio,
                },
                response_payload=provider_response,
            )
            return image

        except GeminiImageClientError as exc:
            generation_ms = int((time.perf_counter() - started) * 1000)
            failed_image = await self.repo.create_generated_image(
                GeneratedImage(
                    user_id=current_user.id,
                    thread_id=thread.id,
                    prompt=safe_prompt,
                    enhanced_prompt=enhanced_prompt,
                    image_url="",
                    status="failed",
                    generation_time_ms=generation_ms,
                    style=payload.style,
                    aspect_ratio=payload.aspect_ratio,
                    model_name=settings.IMAGE_GEN_MODEL,
                    error_message=str(exc),
                )
            )
            await self._write_log(
                generated_image_id=failed_image.id,
                user_id=current_user.id,
                thread_id=thread.id,
                status="failed",
                event_type="generate",
                safety_blocked=False,
                provider_latency_ms=generation_ms,
                error_code="provider_error",
                error_message=str(exc),
                request_payload={
                    "prompt": safe_prompt,
                    "enhanced_prompt": enhanced_prompt,
                    "style": payload.style,
                    "aspect_ratio": payload.aspect_ratio,
                },
                response_payload=provider_response,
            )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail={
                    "error": "image_generation_failed",
                    "message": "Image generation provider failed",
                },
            ) from exc

    async def regenerate(
        self,
        *,
        payload: ImageRegenerateRequest,
        current_user: User,
    ) -> GeneratedImage:
        source = await self.repo.get_generated_image_for_user(
            image_id=payload.image_id,
            user_id=current_user.id,
        )
        if source is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "not_found", "message": "Image not found"},
            )

        generate_payload = ImageGenerateRequest(
            prompt=payload.prompt_override or source.prompt,
            thread_id=source.thread_id,
            style=payload.style or (source.style or "none"),
            aspect_ratio=payload.aspect_ratio or (source.aspect_ratio or "1:1"),
            enhance_prompt=payload.enhance_prompt,
        )
        regenerated = await self.generate(payload=generate_payload, current_user=current_user)
        regenerated.source_image_id = source.id
        self.db.add(regenerated)
        await self.db.commit()
        await self.db.refresh(regenerated)
        return regenerated

    async def list_thread_images(
        self,
        *,
        thread_id: UUID,
        current_user: User,
        limit: int = 100,
        offset: int = 0,
    ) -> list[GeneratedImage]:
        await thread_service.get_thread_for_user(self.db, thread_id, current_user.id)
        return await self.repo.list_thread_images_for_user(
            thread_id=thread_id,
            user_id=current_user.id,
            limit=limit,
            offset=offset,
        )

    async def delete_image(
        self,
        *,
        image_id: UUID,
        current_user: User,
    ) -> None:
        image = await self.repo.get_generated_image_for_user(
            image_id=image_id,
            user_id=current_user.id,
        )
        if image is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "not_found", "message": "Image not found"},
            )

        self._delete_image_file_if_local(image.image_url)
        await self.repo.delete_generated_image(image)
        await self._write_log(
            generated_image_id=None,
            user_id=current_user.id,
            thread_id=image.thread_id,
            status="deleted",
            event_type="delete",
            safety_blocked=False,
            request_payload={"image_id": str(image_id)},
            response_payload=None,
        )

    async def _resolve_thread(self, thread_id: UUID | None, user: User):
        if thread_id is None:
            return await thread_service.create_thread(self.db, user_id=user.id)
        return await thread_service.get_thread_for_user(self.db, thread_id, user.id)

    @staticmethod
    def _sanitize_prompt(prompt: str) -> str:
        sanitized = re.sub(r"\s+", " ", prompt).strip()
        if not sanitized:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"error": "invalid_prompt", "message": "Prompt cannot be empty"},
            )
        if len(sanitized) > settings.IMAGE_GEN_PROMPT_MAX_LENGTH:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"error": "invalid_prompt", "message": "Prompt too long"},
            )
        return sanitized

    @staticmethod
    def _enhance_prompt(*, prompt: str, style: str, aspect_ratio: str, enabled: bool) -> str:
        if not enabled:
            return prompt
        style_hint = _STYLE_HINTS.get(style, "")
        suffix = [
            "high quality",
            "safe for work",
            f"aspect ratio {aspect_ratio}",
        ]
        if style_hint:
            suffix.insert(0, style_hint)
        return f"{prompt}. {'; '.join(suffix)}"

    @staticmethod
    def _validate_prompt_safety(prompt: str) -> None:
        lowered = prompt.lower()
        for term in _BLOCKED_TERMS:
            if term in lowered:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error": "safety_blocked",
                        "message": "Prompt violates content safety policy",
                    },
                )

    def _persist_generated_image(self, *, image_bytes: bytes, mime_type: str) -> str:
        upload_dir = self._generated_upload_dir()
        upload_dir.mkdir(parents=True, exist_ok=True)

        ext = self._extension_for_mime(mime_type)
        digest = hashlib.sha1(image_bytes).hexdigest()[:12]  # noqa: S324
        filename = f"img_{uuid.uuid4().hex}_{digest}.{ext}"
        path = upload_dir / filename
        path.write_bytes(image_bytes)
        return f"/uploads/generated/{filename}"

    @staticmethod
    def _extension_for_mime(mime_type: str) -> str:
        normalized = mime_type.lower()
        if "jpeg" in normalized or "jpg" in normalized:
            return "jpg"
        if "webp" in normalized:
            return "webp"
        return "png"

    @staticmethod
    def _generated_upload_dir() -> Path:
        configured = Path(settings.UPLOAD_DIR)
        if configured.is_absolute():
            base = configured
        else:
            backend_root = Path(__file__).resolve().parents[3]
            base = (backend_root / configured).resolve()
        return base / "generated"

    def _delete_image_file_if_local(self, image_url: str) -> None:
        if not image_url or not image_url.startswith("/uploads/generated/"):
            return
        filename = image_url.rsplit("/", 1)[-1]
        path = self._generated_upload_dir() / filename
        path.unlink(missing_ok=True)

    async def _write_log(
        self,
        *,
        generated_image_id: UUID | None,
        user_id: UUID,
        thread_id: UUID | None,
        status: str,
        event_type: str,
        safety_blocked: bool,
        provider_latency_ms: int | None = None,
        error_code: str | None = None,
        error_message: str | None = None,
        request_payload: dict | None = None,
        response_payload: dict | None = None,
    ) -> None:
        await self.repo.create_log(
            ImageGenerationLog(
                generated_image_id=generated_image_id,
                user_id=user_id,
                thread_id=thread_id,
                status=status,
                event_type=event_type,
                safety_blocked=safety_blocked,
                provider_latency_ms=provider_latency_ms,
                error_code=error_code,
                error_message=error_message,
                request_payload=request_payload,
                response_payload=response_payload,
            )
        )
