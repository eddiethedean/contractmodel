"""Tests for diff engine edge cases."""

from contractmodel.core.ccm import CanonicalContract
from contractmodel.core.types import CompatibilityMode
from contractmodel.diff.engine import diff_contracts
from contractmodel.diff.rules import (
    is_added_field_breaking,
    is_constraint_loosening,
    is_removed_field_breaking,
)


def test_diff_forward_mode_optional_add() -> None:
    old = CanonicalContract.model_validate(
        {
            "contract_id": "a",
            "name": "A",
            "version": "1.0.0",
            "schema": {"fields": [{"name": "id", "logical_type": "string", "required": True}]},
        }
    )
    new = CanonicalContract.model_validate(
        {
            "contract_id": "a",
            "name": "A",
            "version": "2.0.0",
            "schema": {
                "fields": [
                    {"name": "id", "logical_type": "string", "required": True},
                    {"name": "extra", "logical_type": "string", "required": True},
                ]
            },
        }
    )
    result = diff_contracts(old, new, mode=CompatibilityMode.FORWARD)
    assert result.is_breaking is True


def test_diff_full_mode() -> None:
    old = CanonicalContract.model_validate(
        {
            "contract_id": "a",
            "name": "A",
            "version": "1.0.0",
            "schema": {"fields": []},
        }
    )
    new = CanonicalContract.model_validate(
        {
            "contract_id": "a",
            "name": "A",
            "version": "2.0.0",
            "schema": {
                "fields": [{"name": "id", "logical_type": "string", "required": True}]
            },
        }
    )
    result = diff_contracts(old, new, mode=CompatibilityMode.FULL)
    assert result.is_breaking is True


def test_rules_loosening_and_full_add() -> None:
    from contractmodel.core.constraints import FieldConstraints

    old_c = FieldConstraints(
        min_value=10,
        max_value=100,
        min_length=5,
        max_length=20,
        unique=True,
        pattern="a",
        immutable=True,
    )
    new_c = FieldConstraints(
        min_value=1,
        max_value=200,
        min_length=1,
        max_length=50,
        unique=False,
        pattern=None,
        immutable=False,
    )
    assert is_constraint_loosening(old_c, new_c) is True

    field = CanonicalContract.model_validate(
        {
            "contract_id": "x",
            "name": "X",
            "version": "1.0.0",
            "schema": {"fields": [{"name": "id", "logical_type": "string", "required": True}]},
        }
    ).contract_schema.fields[0]
    assert is_added_field_breaking(field, mode=CompatibilityMode.FULL) is True
    assert is_removed_field_breaking(field, mode=CompatibilityMode.FORWARD) is False
