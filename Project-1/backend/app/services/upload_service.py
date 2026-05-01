"""Attachment upload service."""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

from app.core import settings

_ALLOWED_MIME_TO_TYPE = {
    "image/png": "image",
    "image/jpeg": "image",
    "image/webp": "image",
    "video/mp4": "video",
    "video/quicktime": "video",  # .mov
}

_SAFE_NAME_RE = re.compile(r"[^a-zA-Z0-9._-]+")


@dataclass
class SavedUpload:
    attachment_type: str
    attachment_url: str
    name: str
    mime_type: str
    size_bytes: int


def _sanitize_filename(filename: str) -> str:
    cleaned = _SAFE_NAME_RE.sub("_", filename).strip("._")
    return cleaned or "attachment"


def _attachment_type_for_mime(mime_type: str) -> str:
    attachment_type = _ALLOWED_MIME_TO_TYPE.get(mime_type.lower())
    if not attachment_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "unsupported_file_type",
                "message": "Unsupported file MIME type.",
            },
        )
    return attachment_type


async def save_upload(file: UploadFile) -> SavedUpload:
    """Validate and persist an uploaded file to UPLOAD_DIR."""
    mime_type = (file.content_type or "").lower()
    attachment_type = _attachment_type_for_mime(mime_type)

    safe_name = _sanitize_filename(file.filename or "attachment")
    ext = Path(safe_name).suffix
    generated_name = f"{uuid.uuid4().hex}{ext}"

    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    out_path = upload_dir / generated_name

    max_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024
    size = 0

    with out_path.open("wb") as f:
        while True:
            chunk = await file.read(1024 * 1024)
            if not chunk:
                break
            size += len(chunk)
            if size > max_bytes:
                f.close()
                out_path.unlink(missing_ok=True)
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail={
                        "error": "file_too_large",
                        "message": f"File exceeds {settings.MAX_UPLOAD_MB} MB limit.",
                    },
                )
            f.write(chunk)

    await file.close()

    return SavedUpload(
        attachment_type=attachment_type,
        attachment_url=f"/uploads/{generated_name}",
        name=safe_name,
        mime_type=mime_type,
        size_bytes=size,
    )
