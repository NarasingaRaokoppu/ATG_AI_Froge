"""Schemas for Project 9 image compliance checks."""

from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field


Operator = Literal[
    "eq",
    "neq",
    "gt",
    "gte",
    "lt",
    "lte",
    "in",
    "contains",
    "regex",
    "exists",
]


class ImageInput(BaseModel):
    """An image reference previously uploaded through /api/upload."""

    attachment_url: str = Field(..., min_length=1, max_length=2048)
    name: str | None = Field(default=None, max_length=255)


class RuleCondition(BaseModel):
    """A single condition for a rule."""

    field: str = Field(..., min_length=1, max_length=200)
    operator: Operator
    value: Any | None = None


class ComplianceRule(BaseModel):
    """A compliance rule evaluated against extracted image fields."""

    id: str = Field(..., min_length=1, max_length=80)
    description: str = Field(..., min_length=1, max_length=400)
    logic: Literal["and", "or"] = "and"
    conditions: list[RuleCondition] = Field(default_factory=list, min_length=1)


class ImageComplianceEvaluateRequest(BaseModel):
    """Payload for batch compliance checks."""

    thread_id: UUID | None = None
    rule_set_name: str = Field(default="default-rule-set", min_length=1, max_length=255)
    rules: list[ComplianceRule] = Field(default_factory=list, min_length=1)
    images: list[ImageInput] = Field(default_factory=list, min_length=1)


class RuleEvaluation(BaseModel):
    """Result of a single rule evaluation."""

    rule_id: str
    passed: bool
    violations: list[str] = Field(default_factory=list)


class ImageEvaluationResult(BaseModel):
    """Evaluation payload for one image."""

    image_name: str
    image_url: str
    extracted: dict[str, Any] = Field(default_factory=dict)
    passed: bool
    rule_results: list[RuleEvaluation] = Field(default_factory=list)


class ImageComplianceEvaluateResponse(BaseModel):
    """Batch evaluation response."""

    run_id: UUID
    rule_set_name: str
    passed_count: int
    failed_count: int
    results: list[ImageEvaluationResult]
