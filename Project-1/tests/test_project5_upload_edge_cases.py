import pytest
from fastapi import HTTPException

from app.services.upload_service import _attachment_type_for_mime


def test_attachment_type_prefers_extension_when_mime_is_generic() -> None:
    attachment_type = _attachment_type_for_mime("application/octet-stream", "sample.xlsx")
    assert attachment_type == "excel"


def test_attachment_type_rejects_unknown_file_type() -> None:
    with pytest.raises(HTTPException) as exc_info:
        _attachment_type_for_mime("application/octet-stream", "archive.bin")

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail["error"] == "unsupported_file_type"
