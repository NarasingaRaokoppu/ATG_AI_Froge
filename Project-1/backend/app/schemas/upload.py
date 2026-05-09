"""Upload schemas."""

from typing import Literal

from pydantic import BaseModel

AttachmentType = Literal["image", "video", "excel", "docx", "txt"]


class UploadResponse(BaseModel):
    """Uploaded file metadata returned to frontend."""

    attachment_type: AttachmentType
    attachment_url: str
    name: str
    mime_type: str
    size_bytes: int
    content: str | None = None  # For text-based files (txt, excel, docx)
    video_frames: list[str] | None = None  # Base64 data URIs for extracted video frames
