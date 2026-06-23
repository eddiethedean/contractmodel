"""Tests for nested diff."""

from contractmodel import DataContract
from contractmodel.core.ccm import CanonicalContract


def test_nested_field_change_detected() -> None:
    old = DataContract.from_ccm(
        CanonicalContract.model_validate(
            {
                "contract_id": "nested",
                "name": "Nested",
                "version": "1.0.0",
                "schema": {
                    "fields": [
                        {
                            "name": "address",
                            "logical_type": "object",
                            "children": [{"name": "city", "logical_type": "string"}],
                        }
                    ]
                },
            }
        )
    )
    new = DataContract.from_ccm(
        CanonicalContract.model_validate(
            {
                "contract_id": "nested",
                "name": "Nested",
                "version": "2.0.0",
                "schema": {
                    "fields": [
                        {
                            "name": "address",
                            "logical_type": "object",
                            "children": [
                                {"name": "city", "logical_type": "string"},
                                {"name": "zip", "logical_type": "string"},
                            ],
                        }
                    ]
                },
            }
        )
    )
    diff = old.diff(new)
    assert any("address.zip" in change.field for change in diff.breaking_changes)
