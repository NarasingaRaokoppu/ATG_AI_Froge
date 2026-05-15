"""Google Sheets loading service."""

from __future__ import annotations

import json
import re
from functools import lru_cache

import gspread
import pandas as pd
from fastapi import HTTPException, status

from app.core import settings


_SHEET_ID_RE = re.compile(r"/spreadsheets/d/([a-zA-Z0-9-_]+)")


def _extract_spreadsheet_id(*, url: str | None, spreadsheet_id: str | None) -> str:
    if spreadsheet_id:
        return spreadsheet_id.strip()
    if not url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "missing_google_sheet",
                "message": "Google Sheet URL or spreadsheet ID is required",
            },
        )
    match = _SHEET_ID_RE.search(url)
    if not match:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "invalid_google_sheet_url",
                "message": "Invalid Google Sheet URL",
            },
        )
    return match.group(1)


@lru_cache(maxsize=1)
def _service_account_client() -> gspread.Client:
    raw = settings.GOOGLE_SERVICE_ACCOUNT_JSON
    if not raw:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "missing_google_service_account",
                "message": "GOOGLE_SERVICE_ACCOUNT_JSON is not configured",
            },
        )
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "invalid_google_service_account",
                "message": "GOOGLE_SERVICE_ACCOUNT_JSON must be valid JSON",
            },
        ) from exc
    return gspread.service_account_from_dict(data)


def load_google_sheet_dataframe(
    *,
    url: str | None,
    spreadsheet_id: str | None,
    worksheet_title: str | None = None,
) -> tuple[pd.DataFrame, str, str | None]:
    """Load a worksheet into a dataframe via gspread."""
    client = _service_account_client()
    resolved_id = _extract_spreadsheet_id(url=url, spreadsheet_id=spreadsheet_id)
    spreadsheet = client.open_by_key(resolved_id)
    worksheet = spreadsheet.worksheet(worksheet_title) if worksheet_title else spreadsheet.sheet1
    return (
        pd.DataFrame(worksheet.get_all_records()),
        f"https://docs.google.com/spreadsheets/d/{resolved_id}",
        worksheet.title,
    )
