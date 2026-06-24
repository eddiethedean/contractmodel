"""Tests for nested diff."""

from contractmodel import DataContract
from contractmodel.core.ccm import CanonicalContract
from contractmodel.core.types import CompatibilityMode


def _nested_address_contract(*, version: str, children: list[dict]) -> DataContract:
    return DataContract.from_ccm(
        CanonicalContract.model_validate(
            {
                "contract_id": "nested",
                "name": "Nested",
                "version": version,
                "schema": {
                    "fields": [
                        {
                            "name": "address",
                            "logical_type": "object",
                            "children": children,
                        }
                    ]
                },
            }
        )
    )


def test_nested_field_change_detected() -> None:
    old = _nested_address_contract(
        version="1.0.0",
        children=[{"name": "city", "logical_type": "string"}],
    )
    new = _nested_address_contract(
        version="2.0.0",
        children=[
            {"name": "city", "logical_type": "string"},
            {"name": "zip", "logical_type": "string", "required": True},
        ],
    )
    diff = old.diff(new)
    assert any("address.zip" in change.field for change in diff.breaking_changes)


def test_diff_forward_mode_optional_nested_add_non_breaking() -> None:
    old = _nested_address_contract(
        version="1.0.0",
        children=[{"name": "city", "logical_type": "string"}],
    )
    new = _nested_address_contract(
        version="2.0.0",
        children=[
            {"name": "city", "logical_type": "string"},
            {"name": "zip", "logical_type": "string", "required": False, "nullable": True},
        ],
    )
    diff = old.diff(new, mode=CompatibilityMode.FORWARD)
    assert diff.is_breaking is False
    assert any("address.zip" in change.field for change in diff.non_breaking_changes)

