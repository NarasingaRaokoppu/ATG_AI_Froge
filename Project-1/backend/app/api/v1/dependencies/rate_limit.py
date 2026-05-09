"""Simple in-memory rate limiter dependency for image generation endpoints."""

from __future__ import annotations

import asyncio
import time
from collections import defaultdict, deque
from uuid import UUID

from fastapi import HTTPException, status

# Per-process limiter. Replace with Redis for multi-instance production.
_user_hits: dict[UUID, deque[float]] = defaultdict(deque)
_limiter_lock = asyncio.Lock()


async def enforce_image_generation_rate_limit(
    user_id: UUID,
    *,
    max_requests: int = 10,
    per_seconds: int = 60,
) -> None:
    """Allow up to `max_requests` in the trailing `per_seconds` window."""
    now = time.monotonic()
    window_start = now - per_seconds

    async with _limiter_lock:
        history = _user_hits[user_id]
        while history and history[0] < window_start:
            history.popleft()

        if len(history) >= max_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "rate_limited",
                    "message": "Image generation rate limit exceeded",
                },
            )

        history.append(now)
