"""Tests for validation modes."""

from contractmodel.core.ccm import CanonicalContract
from contractmodel.core.types import ValidationMode
from contractmodel.validation.engine import validate_record


def _contract() -> CanonicalContract:
    return CanonicalContract.model_validate(
        {
            "contract_id": "modes",
            "name": "Modes",
            "version": "1.0.0",
            "schema": {
                "fields": [
                    {
                        "name": "score",
                        "logical_type": "integer",
                        "required": True,
                        "constraints": {"min_value": 0, "max_value": 10},
                    }
                ]
            },
        }
    )


def test_strict_rejects_extra_field() -> None:
    result = validate_record(_contract(), {"score": 5, "extra": 1}, mode=ValidationMode.STRICT)
    assert result.success is False
    assert any(error.code == "CM_SCHEMA_EXTRA_FIELD" for error in result.errors)


def test_permissive_allows_extra_field() -> None:
    result = validate_record(_contract(), {"score": 5, "extra": 1}, mode=ValidationMode.PERMISSIVE)
    assert result.success is True


def test_schema_only_ignores_constraints() -> None:
    result = validate_record(_contract(), {"score": 99}, mode=ValidationMode.SCHEMA_ONLY)
    assert result.success is True


def test_quality_only_runs_quality_rules() -> None:
    contract = CanonicalContract.model_validate(
        {
            "contract_id": "quality",
            "name": "Quality",
            "version": "1.0.0",
            "schema": {"fields": [{"name": "id", "logical_type": "string", "required": True}]},
            "quality": {"rules": [{"name": "complete", "type": "completeness"}]},
        }
    )
    result = validate_record(contract, {}, mode=ValidationMode.QUALITY_ONLY)
    assert result.success is False
    assert any(error.code == "CM_QUALITY_COMPLETENESS" for error in result.errors)


def test_strict_no_duplicate_extra_errors() -> None:
    result = validate_record(_contract(), {"score": 5, "extra": 1}, mode=ValidationMode.STRICT)
    extra_errors = [e for e in result.errors if e.code == "CM_SCHEMA_EXTRA_FIELD"]
    assert len(extra_errors) == 1
