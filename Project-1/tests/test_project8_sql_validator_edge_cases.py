import pytest
from fastapi import HTTPException

from app.services.sql_validator import validate_and_normalize_sql


def test_sql_validator_adds_limit_when_missing() -> None:
    sql = validate_and_normalize_sql("SELECT id, email FROM users", max_limit=25)
    assert sql.endswith("LIMIT 25")


def test_sql_validator_rejects_semicolon_in_middle() -> None:
    with pytest.raises(HTTPException) as exc_info:
        validate_and_normalize_sql("SELECT * FROM users; SELECT * FROM threads")

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail["error"] == "unsafe_sql"


def test_sql_validator_rejects_write_keyword() -> None:
    with pytest.raises(HTTPException) as exc_info:
        validate_and_normalize_sql("DELETE FROM users")

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail["message"] == "Only SELECT or WITH queries are allowed"
