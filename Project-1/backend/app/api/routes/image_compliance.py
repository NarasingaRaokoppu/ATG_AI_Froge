"""Project 9 routes for image extraction and compliance checks."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db import get_db
from app.models import ImageComplianceAudit, User
from app.schemas.image_compliance import (
    ImageComplianceEvaluateRequest,
    ImageComplianceEvaluateResponse,
)
from app.services import image_compliance_service

router = APIRouter(prefix="/image-compliance", tags=["image-compliance"])


@router.post("/evaluate", response_model=ImageComplianceEvaluateResponse)
async def evaluate_images(
    payload: ImageComplianceEvaluateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ImageComplianceEvaluateResponse:
    """Evaluate a set of images against rule definitions and persist an audit."""
    return await image_compliance_service.evaluate_image_compliance(
        db,
        current_user=current_user,
        payload=payload,
    )


@router.get("/runs", response_model=list[dict])
async def list_runs(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(default=20, ge=1, le=100),
) -> list[dict]:
    """List recent compliance runs for the current user."""
    runs = await image_compliance_service.list_compliance_audits(
        db,
        current_user=current_user,
        limit=limit,
    )
    return [_to_run_payload(item) for item in runs]


@router.get("/runs/{run_id}", response_model=dict)
async def get_run(
    run_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """Get a single compliance run."""
    run = await image_compliance_service.get_compliance_audit(
        db,
        current_user=current_user,
        run_id=run_id,
    )
    return _to_run_payload(run)


def _to_run_payload(run: ImageComplianceAudit) -> dict:
    return {
        "id": str(run.id),
        "thread_id": str(run.thread_id) if run.thread_id else None,
        "rule_set_name": run.rule_set_name,
        "passed_count": run.passed_count,
        "failed_count": run.failed_count,
        "rules": run.rules,
        "input_images": run.input_images,
        "results": run.results,
        "created_at": run.created_at,
    }
