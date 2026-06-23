"""Tests for diff rules."""

import copy

from contractmodel import DataContract
from contractmodel.core.ccm import CanonicalContract
from contractmodel.core.types import CompatibilityMode
from contractmodel.diff.rules import (
    classify_field_change,
    is_added_field_breaking,
    is_constraint_tightening,
)


def test_required_field_add_is_breaking_backward() -> None:
    field = CanonicalContract.model_validate(
        {
            "contract_id": "x",
            "name": "X",
            "version": "1.0.0",
            "schema": {"fields": [{"name": "id", "logical_type": "string", "required": True}]},
        }
    ).contract_schema.fields[0]
    assert is_added_field_breaking(field, mode=CompatibilityMode.BACKWARD) is True


def test_constraint_tightening_detected() -> None:
    old = CanonicalContract.model_validate(
        {
            "contract_id": "x",
            "name": "X",
            "version": "1.0.0",
            "schema": {
                "fields": [
                    {
                        "name": "score",
                        "logical_type": "integer",
                        "constraints": {"max_value": 100},
                    }
                ]
            },
        }
    ).contract_schema.fields[0]
    new = copy.deepcopy(old)
    new.constraints.max_value = 50
    assert is_constraint_tightening(old.constraints, new.constraints) is True


def test_classify_nullable_to_required_is_breaking() -> None:
    old = CanonicalContract.model_validate(
        {
            "contract_id": "x",
            "name": "X",
            "version": "1.0.0",
            "schema": {
                "fields": [
                    {"name": "id", "logical_type": "string", "required": False, "nullable": True}
                ]
            },
        }
    ).contract_schema.fields[0]
    new = copy.deepcopy(old)
    new.required = True
    new.nullable = False
    breaking, _ = classify_field_change(old, new)
    assert any("optional to required" in message for message in breaking)


def test_rename_via_alias_is_non_breaking() -> None:
    old = DataContract.from_ccm(
        CanonicalContract.model_validate(
            {
                "contract_id": "x",
                "name": "X",
                "version": "1.0.0",
                "schema": {
                    "fields": [
                        {
                            "name": "customer_id",
                            "logical_type": "string",
                            "required": True,
                            "aliases": ["client_id"],
                        }
                    ]
                },
            }
        )
    )
    new = DataContract.from_ccm(
        CanonicalContract.model_validate(
            {
                "contract_id": "x",
                "name": "X",
                "version": "2.0.0",
                "schema": {
                    "fields": [
                        {
                            "name": "client_id",
                            "logical_type": "string",
                            "required": True,
                            "aliases": ["customer_id"],
                        }
                    ]
                },
            }
        )
    )
    diff = old.diff(new)
    assert diff.is_breaking is False
    assert any("renamed" in change.message for change in diff.non_breaking_changes)
