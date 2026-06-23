"""Tests for validation uniqueness and generator consumption."""

from contractmodel.core.ccm import CanonicalContract
from contractmodel.validation.engine import validate_records


def _contract_with_unique() -> CanonicalContract:
    return CanonicalContract.model_validate(
        {
            "contract_id": "unique",
            "name": "Unique",
            "version": "1.0.0",
            "schema": {
                "fields": [
                    {
                        "name": "id",
                        "logical_type": "string",
                        "constraints": {"unique": True},
                    }
                ]
            },
        }
    )


def test_uniqueness_with_generator() -> None:
    contract = _contract_with_unique()

    def records():
        yield {"id": "a"}
        yield {"id": "a"}

    result = validate_records(contract, records())
    assert result.success is False
    assert any(error.code == "CM_DATASET_UNIQUE" for error in result.errors)


def test_uniqueness_ignores_nulls() -> None:
    contract = CanonicalContract.model_validate(
        {
            "contract_id": "unique",
            "name": "Unique",
            "version": "1.0.0",
            "schema": {
                "fields": [
                    {
                        "name": "id",
                        "logical_type": "string",
                        "required": False,
                        "nullable": True,
                        "constraints": {"unique": True},
                    }
                ]
            },
        }
    )
    result = validate_records(contract, [{"id": None}, {"id": None}])
    assert result.success is True
