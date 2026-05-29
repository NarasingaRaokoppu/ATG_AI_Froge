from app.schemas.image_compliance import ComplianceRule, RuleCondition
from app.services.image_compliance_service import _evaluate_rule


def test_project9_rule_fails_when_required_field_missing() -> None:
    rule = ComplianceRule(
        id="helmet_required",
        description="Helmet required",
        logic="and",
        conditions=[RuleCondition(field="ppe.helmet", operator="eq", value=True)],
    )

    result = _evaluate_rule({}, rule)
    assert result.passed is False
    assert any("missing" in violation for violation in result.violations)


def test_project9_rule_passes_or_logic_when_one_condition_matches() -> None:
    rule = ComplianceRule(
        id="badge_or_vest",
        description="Badge or vest must be present",
        logic="or",
        conditions=[
            RuleCondition(field="person.id_badge", operator="eq", value=True),
            RuleCondition(field="ppe.vest", operator="eq", value=True),
        ],
    )

    extracted = {"person": {"id_badge": False}, "ppe": {"vest": True}}
    result = _evaluate_rule(extracted, rule)
    assert result.passed is True
