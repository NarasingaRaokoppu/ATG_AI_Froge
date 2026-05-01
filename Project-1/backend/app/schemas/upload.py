"""Upload schemas."""

from typing import Literal

from pydantic import BaseModel

AttachmentType = Literal["image", "video"]


class UploadResponse(BaseModel):
    """Uploaded file metadata returned to frontend."""

    attachment_type: AttachmentType
    attachment_url: str
    name: str
    mime_type: str
    size_bytes: int
