"""Additional validation constraint code tests."""

from contractmodel.core.ccm import CanonicalContract
from contractmodel.core.types import ValidationMode
from contractmodel.validation.engine import validate_record


def test_min_length_constraint_code() -> None:
    contract = CanonicalContract.model_validate(
        {
            "contract_id": "x",
            "name": "X",
            "version": "1.0.0",
            "schema": {
                "fields": [
                    {
                        "name": "code",
                        "logical_type": "string",
                        "required": True,
                        "constraints": {"min_length": 3},
                    }
                ]
            },
        }
    )
    result = validate_record(contract, {"code": "ab"}, mode=ValidationMode.STRICT)
    assert result.success is False
    assert any(error.code == "CM_CONSTRAINT_MIN_LENGTH" for error in result.errors)


def test_max_length_constraint_code() -> None:
    contract = CanonicalContract.model_validate(
        {
            "contract_id": "x",
            "name": "X",
            "version": "1.0.0",
            "schema": {
                "fields": [
                    {
                        "name": "code",
                        "logical_type": "string",
                        "required": True,
                        "constraints": {"max_length": 2},
                    }
                ]
            },
        }
    )
    result = validate_record(contract, {"code": "abc"}, mode=ValidationMode.STRICT)
    assert result.success is False
    assert any(error.code == "CM_CONSTRAINT_MAX_LENGTH" for error in result.errors)
