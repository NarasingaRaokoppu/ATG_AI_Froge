"""Read-only SQL validation rules for NL-to-SQL execution."""

from __future__ import annotations

import re

from fastapi import HTTPException, status

_FORBIDDEN_KEYWORDS = {
    "INSERT",
    "UPDATE",
    "DELETE",
    "DROP",
    "ALTER",
    "TRUNCATE",
    "CREATE",
    "GRANT",
    "REVOKE",
}


def _reject(reason: str) -> None:
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail={"error": "unsafe_sql", "message": reason},
    )


def _contains_comments(sql: str) -> bool:
    return "--" in sql or "/*" in sql or "*/" in sql


def _contains_semicolon(sql: str) -> bool:
    return ";" in sql


def _strip_single_trailing_semicolon(sql: str) -> str:
    trimmed = sql.rstrip()
    if trimmed.endswith(";"):
        return trimmed[:-1].rstrip()
    return trimmed


def _starts_with_select_or_with(sql: str) -> bool:
    normalized = sql.lstrip().upper()
    return normalized.startswith("SELECT") or normalized.startswith("WITH")


def _contains_forbidden_keyword(sql: str) -> str | None:
    upper = sql.upper()
    for keyword in _FORBIDDEN_KEYWORDS:
        if re.search(rf"\b{re.escape(keyword)}\b", upper):
            return keyword
    return None


def _has_limit(sql: str) -> bool:
    upper = sql.upper()
    return bool(re.search(r"\bLIMIT\s+\d+\b", upper))


def _append_limit(sql: str, limit: int) -> str:
    return f"{sql.rstrip()} LIMIT {limit}"


def validate_and_normalize_sql(sql: str, *, max_limit: int = 1000) -> str:
    """Validate generated SQL and enforce read-only safety constraints."""
    if not sql or not sql.strip():
        _reject("Generated SQL is empty")

    candidate = sql.strip()
    if candidate.startswith("```"):
        candidate = candidate.strip("`")
        candidate = candidate.replace("sql", "", 1).strip()

    candidate = _strip_single_trailing_semicolon(candidate)

    if _contains_comments(candidate):
        _reject("SQL comments are not allowed")
    if _contains_semicolon(candidate):
        _reject("Semicolons are not allowed")
    if not _starts_with_select_or_with(candidate):
        _reject("Only SELECT or WITH queries are allowed")

    forbidden = _contains_forbidden_keyword(candidate)
    if forbidden:
        _reject(f"Forbidden SQL keyword detected: {forbidden}")

    if not _has_limit(candidate):
        candidate = _append_limit(candidate, max_limit)

    return candidate
