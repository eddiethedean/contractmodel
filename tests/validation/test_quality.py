"""Tests for quality rule validation."""

from contractmodel.core.ccm import CanonicalContract
from contractmodel.validation.quality import validate_quality_rules


def test_completeness_rule_fails() -> None:
    contract = CanonicalContract.model_validate(
        {
            "contract_id": "q",
            "name": "Q",
            "version": "1.0.0",
            "schema": {"fields": [{"name": "id", "logical_type": "string", "required": True}]},
            "quality": {"rules": [{"name": "complete", "type": "completeness"}]},
        }
    )
    result = validate_quality_rules(contract, [{"id": None}])
    assert result.success is False
    assert result.errors[0].code == "CM_QUALITY_COMPLETENESS"


def test_freshness_rule_warning() -> None:
    contract = CanonicalContract.model_validate(
        {
            "contract_id": "q",
            "name": "Q",
            "version": "1.0.0",
            "schema": {"fields": []},
            "quality": {"rules": [{"name": "fresh", "type": "freshness"}]},
        }
    )
    result = validate_quality_rules(contract, [])
    assert result.warning_count == 1
    assert result.warnings[0].code == "CM_QUALITY_FRESHNESS"
