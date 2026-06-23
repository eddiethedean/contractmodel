"""Tests for CCM validation."""

import pytest
from pydantic import ValidationError

from contractmodel.core.ccm import CanonicalContract, ContractField, ContractSchema
from contractmodel.core.types import LogicalType


def _minimal_contract_data() -> dict:
    return {
        "contract_id": "test",
        "name": "Test",
        "version": "1.0.0",
        "schema": {
            "fields": [
                {
                    "name": "id",
                    "logical_type": "string",
                }
            ]
        },
    }


def test_valid_minimal_contract() -> None:
    contract = CanonicalContract.model_validate(_minimal_contract_data())
    assert contract.schema.fields[0].name == "id"


def test_missing_required_top_level_field() -> None:
    data = _minimal_contract_data()
    del data["contract_id"]
    with pytest.raises(ValidationError):
        CanonicalContract.model_validate(data)


def test_invalid_logical_type() -> None:
    data = _minimal_contract_data()
    data["schema"]["fields"][0]["logical_type"] = "not_a_type"
    with pytest.raises(ValidationError):
        CanonicalContract.model_validate(data)


def test_nested_children() -> None:
    contract = CanonicalContract.model_validate(
        {
            "contract_id": "nested",
            "name": "Nested",
            "version": "1.0.0",
            "schema": {
                "fields": [
                    {
                        "name": "address",
                        "logical_type": "object",
                        "children": [
                            {
                                "name": "city",
                                "logical_type": "string",
                            }
                        ],
                    }
                ]
            },
        }
    )
    address = contract.schema.fields[0]
    assert address.logical_type == LogicalType.OBJECT
    assert len(address.children) == 1
    assert address.children[0].name == "city"


def test_contract_field_defaults() -> None:
    field = ContractField(name="x", logical_type=LogicalType.STRING)
    assert field.required is True
    assert field.nullable is False
    assert field.constraints.enum_values is None


def test_contract_schema_requires_fields_key() -> None:
    with pytest.raises(ValidationError):
        ContractSchema.model_validate({})
