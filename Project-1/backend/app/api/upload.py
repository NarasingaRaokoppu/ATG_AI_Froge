"""Upload routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile

from app.core.security import get_current_user
from app.models import User
from app.schemas.upload import UploadResponse
from app.services import upload_service

router = APIRouter(prefix="/upload", tags=["upload"])


@router.post("", response_model=UploadResponse)
async def upload_attachment(
    current_user: Annotated[User, Depends(get_current_user)],
    file: UploadFile = File(...),
) -> UploadResponse:
    """Upload an attachment (image, video, excel, docx, txt) and return metadata.
    
    For binary files: stored on disk with URL.
    For text files: content parsed and included in response.
    For videos: key frames extracted and included as base64 data URIs.
    """
    _ = current_user
    saved = await upload_service.save_upload(file)

    return UploadResponse(
        attachment_type=saved.attachment_type,
        attachment_url=saved.attachment_url,
        name=saved.name,
        mime_type=saved.mime_type,
        size_bytes=saved.size_bytes,
        content=saved.content,
        video_frames=saved.video_frames,
    )
