"""Gemini image generation client wrapper with retries and normalization."""

from __future__ import annotations

import asyncio
import base64
import binascii
from dataclasses import dataclass

import httpx

from app.ai.llm import client
from app.core import settings


class GeminiImageClientError(RuntimeError):
    """Raised when image generation fails."""


@dataclass
class GeminiImageResult:
    """Normalized output from provider response."""

    image_bytes: bytes
    mime_type: str
    raw_response: dict


class GeminiImageClient:
    """Wrapper over LiteLLM/OpenAI SDK for Gemini image generation."""

    def __init__(self, model_name: str | None = None, max_retries: int | None = None):
        self.model_name = model_name or settings.IMAGE_GEN_MODEL
        self.max_retries = max_retries if max_retries is not None else settings.IMAGE_GEN_MAX_RETRIES

    async def generate_image(
        self,
        *,
        prompt: str,
        aspect_ratio: str,
        user_email: str,
    ) -> GeminiImageResult:
        """Generate image bytes using the configured image model."""
        last_error: Exception | None = None

        for attempt in range(self.max_retries + 1):
            try:
                response = await asyncio.to_thread(
                    client.images.generate,
                    model=self.model_name,
                    prompt=prompt,
                    size=self._size_for_aspect_ratio(aspect_ratio),
                    response_format="b64_json",
                    extra_body={
                        "metadata": {
                            "user_email": user_email,
                            "application": settings.APP_NAME,
                            "environment": settings.ENVIRONMENT,
                            "aspect_ratio": aspect_ratio,
                        }
                    },
                )
                return await self._normalize_response(response)
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                if attempt >= self.max_retries:
                    break
                await asyncio.sleep(0.5 * (2 ** attempt))

        raise GeminiImageClientError(f"Image generation failed: {last_error}")

    @staticmethod
    def _size_for_aspect_ratio(aspect_ratio: str) -> str:
        mapping = {
            "1:1": "1024x1024",
            "16:9": "1536x864",
            "9:16": "864x1536",
            "4:3": "1152x864",
            "3:4": "864x1152",
        }
        return mapping.get(aspect_ratio, "1024x1024")

    async def _normalize_response(self, response: object) -> GeminiImageResult:
        """Accept provider url/base64 payloads and normalize to bytes."""
        data = getattr(response, "data", None)
        if not data:
            raise GeminiImageClientError("Provider returned an empty image payload")

        first_item = data[0]
        b64_payload = getattr(first_item, "b64_json", None)
        if b64_payload:
            try:
                image_bytes = base64.b64decode(b64_payload)
            except binascii.Error as exc:
                raise GeminiImageClientError("Invalid base64 image from provider") from exc
            return GeminiImageResult(
                image_bytes=image_bytes,
                mime_type="image/png",
                raw_response=self._serialize_response(response),
            )

        remote_url = getattr(first_item, "url", None)
        if remote_url:
            async with httpx.AsyncClient(timeout=30.0) as http_client:
                downloaded = await http_client.get(remote_url)
                downloaded.raise_for_status()
                mime_type = downloaded.headers.get("content-type", "image/png")
                return GeminiImageResult(
                    image_bytes=downloaded.content,
                    mime_type=mime_type,
                    raw_response=self._serialize_response(response),
                )

        raise GeminiImageClientError("Unsupported provider response format")

    @staticmethod
    def _serialize_response(response: object) -> dict:
        if hasattr(response, "model_dump"):
            return response.model_dump(mode="json")  # type: ignore[no-any-return]
        if hasattr(response, "dict"):
            return response.dict()  # type: ignore[no-any-return]
        return {"response": str(response)}
