"""Project 9 image extraction + rule compliance service."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from langchain_core.messages import HumanMessage
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.chains.chat_chain import chat_llm
from app.core import settings
from app.models import ImageComplianceAudit, User
from app.schemas.image_compliance import (
    ComplianceRule,
    ImageComplianceEvaluateRequest,
    ImageComplianceEvaluateResponse,
    ImageEvaluationResult,
    RuleCondition,
    RuleEvaluation,
)
from app.services import thread_service


def _upload_dir_path() -> Path:
    configured = Path(settings.UPLOAD_DIR)
    if configured.is_absolute():
        return configured
    backend_root = Path(__file__).resolve().parents[2]
    return (backend_root / configured).resolve()


def _safe_image_path(attachment_url: str) -> Path:
    relative = attachment_url.strip().lstrip("/")
    if relative.startswith("uploads/"):
        relative = relative[len("uploads/") :]
    filename = Path(relative).name
    candidate = (_upload_dir_path() / filename).resolve()
    if not candidate.exists() or not candidate.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "image_not_found",
                "message": f"Uploaded image not found for {attachment_url}",
            },
        )
    return candidate


def _to_data_uri(path: Path) -> str:
    import base64
    import mimetypes

    mime = mimetypes.guess_type(str(path))[0] or "image/png"
    payload = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{payload}"


def _extract_json_object(raw: str) -> dict[str, Any]:
    text = raw.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if len(lines) >= 3 and lines[-1].strip() == "```":
            text = "\n".join(lines[1:-1]).strip()

    try:
        decoded = json.loads(text)
        if isinstance(decoded, dict):
            return decoded
    except json.JSONDecodeError:
        pass

    # Fallback: best-effort object extraction from verbose output.
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return {}
    try:
        decoded = json.loads(match.group(0))
        return decoded if isinstance(decoded, dict) else {}
    except json.JSONDecodeError:
        return {}


def _get_nested_value(payload: dict[str, Any], field: str) -> Any:
    value: Any = payload
    for part in field.split("."):
        if not isinstance(value, dict) or part not in value:
            return None
        value = value[part]
    return value


def _to_float(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    return None


def _eval_condition(extracted: dict[str, Any], condition: RuleCondition) -> tuple[bool, str | None]:
    actual = _get_nested_value(extracted, condition.field)
    op = condition.operator
    expected = condition.value

    if op == "exists":
        ok = actual is not None
        return ok, None if ok else f"{condition.field} is missing"

    if actual is None:
        return False, f"{condition.field} is missing"

    if op == "eq":
        ok = actual == expected
    elif op == "neq":
        ok = actual != expected
    elif op in {"gt", "gte", "lt", "lte"}:
        left = _to_float(actual)
        right = _to_float(expected)
        if left is None or right is None:
            return False, f"{condition.field} is not numeric"
        if op == "gt":
            ok = left > right
        elif op == "gte":
            ok = left >= right
        elif op == "lt":
            ok = left < right
        else:
            ok = left <= right
    elif op == "in":
        ok = isinstance(expected, list) and actual in expected
    elif op == "contains":
        if isinstance(actual, list):
            ok = expected in actual
        elif isinstance(actual, str):
            ok = str(expected) in actual
        else:
            ok = False
    elif op == "regex":
        ok = isinstance(actual, str) and isinstance(expected, str) and re.search(expected, actual) is not None
    else:
        ok = False

    if ok:
        return True, None
    return False, f"{condition.field} failed {op} check (actual={actual!r}, expected={expected!r})"


def _evaluate_rule(extracted: dict[str, Any], rule: ComplianceRule) -> RuleEvaluation:
    checks: list[tuple[bool, str | None]] = [_eval_condition(extracted, cond) for cond in rule.conditions]
    if rule.logic == "or":
        passed = any(result for result, _ in checks)
    else:
        passed = all(result for result, _ in checks)

    violations = [msg for ok, msg in checks if not ok and msg]
    return RuleEvaluation(rule_id=rule.id, passed=passed, violations=violations)


async def _extract_fields_with_vision(
    *,
    data_uri: str,
    requested_fields: list[str],
    image_name: str,
) -> dict[str, Any]:
    prompt = (
        "You are an information extraction engine for compliance checks. "
        "Inspect the image and return only valid JSON object, no markdown.\n"
        f"Image name: {image_name}\n"
        f"Extract these fields: {requested_fields}\n"
        "Rules:\n"
        "- Use null when a field is not visible.\n"
        "- Include a top-level key named confidence from 0 to 1.\n"
        "- Keep values concise and factual."
    )

    content: list[dict[str, Any]] = [
        {"type": "text", "text": prompt},
        {"type": "image_url", "image_url": {"url": data_uri}},
    ]

    try:
        response = await chat_llm.ainvoke([HumanMessage(content=content)])
        raw = response.content if isinstance(response.content, str) else str(response.content)
        parsed = _extract_json_object(raw)
        return parsed if parsed else {"confidence": 0.0}
    except Exception:
        return {"confidence": 0.0}


async def evaluate_image_compliance(
    db: AsyncSession,
    *,
    current_user: User,
    payload: ImageComplianceEvaluateRequest,
) -> ImageComplianceEvaluateResponse:
    """Run extraction + rules evaluation and persist an audit row."""
    if payload.thread_id is not None:
        await thread_service.get_thread_for_user(db, payload.thread_id, current_user.id)

    requested_fields = sorted({cond.field for rule in payload.rules for cond in rule.conditions})

    evaluations: list[ImageEvaluationResult] = []
    passed_count = 0
    failed_count = 0

    for image in payload.images:
        image_path = _safe_image_path(image.attachment_url)
        image_name = image.name or image_path.name
        extracted = await _extract_fields_with_vision(
            data_uri=_to_data_uri(image_path),
            requested_fields=requested_fields,
            image_name=image_name,
        )

        rule_results = [_evaluate_rule(extracted, rule) for rule in payload.rules]
        image_passed = all(item.passed for item in rule_results)
        if image_passed:
            passed_count += 1
        else:
            failed_count += 1

        evaluations.append(
            ImageEvaluationResult(
                image_name=image_name,
                image_url=image.attachment_url,
                extracted=extracted,
                passed=image_passed,
                rule_results=rule_results,
            )
        )

    audit = ImageComplianceAudit(
        user_id=current_user.id,
        thread_id=payload.thread_id,
        rule_set_name=payload.rule_set_name,
        rules=[rule.model_dump(mode="json") for rule in payload.rules],
        input_images=[img.model_dump(mode="json") for img in payload.images],
        results=[item.model_dump(mode="json") for item in evaluations],
        passed_count=passed_count,
        failed_count=failed_count,
    )
    db.add(audit)
    await db.commit()
    await db.refresh(audit)

    return ImageComplianceEvaluateResponse(
        run_id=audit.id,
        rule_set_name=audit.rule_set_name,
        passed_count=passed_count,
        failed_count=failed_count,
        results=evaluations,
    )


async def list_compliance_audits(
    db: AsyncSession,
    *,
    current_user: User,
    limit: int = 20,
) -> list[ImageComplianceAudit]:
    """Return recent compliance runs for the current user."""
    from sqlalchemy import select

    result = await db.scalars(
        select(ImageComplianceAudit)
        .where(ImageComplianceAudit.user_id == current_user.id)
        .order_by(ImageComplianceAudit.created_at.desc())
        .limit(limit)
    )
    return list(result)


async def get_compliance_audit(
    db: AsyncSession,
    *,
    current_user: User,
    run_id: UUID,
) -> ImageComplianceAudit:
    """Fetch one compliance run by id with ownership checks."""
    audit = await db.get(ImageComplianceAudit, run_id)
    if audit is None or audit.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "not_found", "message": "Compliance run not found"},
        )
    return audit
