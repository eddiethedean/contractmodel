"""Tests for diff engine."""

import copy
from pathlib import Path

from contractmodel import DataContract
from contractmodel.core.ccm import CanonicalContract
from contractmodel.core.types import LogicalType

EXAMPLES_DIR = Path(__file__).resolve().parents[2] / "examples"


def _base_contract() -> DataContract:
    return DataContract.from_odcs(EXAMPLES_DIR / "customer_events.odcs.yaml")


def test_add_optional_field_non_breaking() -> None:
    old = _base_contract()
    new_ccm = copy.deepcopy(old.ccm)
    new_ccm.contract_schema.fields.append(
        CanonicalContract.model_validate(
            {
                "contract_id": "x",
                "name": "X",
                "version": "1.0.0",
                "schema": {
                    "fields": [
                        {
                            "name": "source",
                            "logical_type": "string",
                            "required": False,
                            "nullable": True,
                        }
                    ]
                },
            }
        ).contract_schema.fields[0]
    )
    new = DataContract.from_ccm(new_ccm)

    diff = old.diff(new)
    assert "source" in diff.added_fields
    assert diff.is_breaking is False


def test_remove_required_field_breaking() -> None:
    old = _base_contract()
    new_ccm = copy.deepcopy(old.ccm)
    new_ccm.contract_schema.fields = [
        f for f in new_ccm.contract_schema.fields if f.name != "customer_id"
    ]
    new = DataContract.from_ccm(new_ccm)

    diff = old.diff(new)
    assert "customer_id" in diff.removed_fields
    assert diff.is_breaking is True


def test_type_change_breaking() -> None:
    old = _base_contract()
    new_ccm = copy.deepcopy(old.ccm)
    customer_id = next(f for f in new_ccm.contract_schema.fields if f.name == "customer_id")
    customer_id.logical_type = LogicalType.INTEGER
    new = DataContract.from_ccm(new_ccm)

    diff = old.diff(new)
    assert diff.is_breaking is True
    assert any(change.field == "customer_id" for change in diff.breaking_changes)


def test_is_breaking_change_helper() -> None:
    old = _base_contract()
    new_ccm = copy.deepcopy(old.ccm)
    new_ccm.contract_schema.fields = [
        f for f in new_ccm.contract_schema.fields if f.name != "event_id"
    ]
    new = DataContract.from_ccm(new_ccm)
    assert old.is_breaking_change(new) is True
    assert old.has_breaking_changes(new) is True


def test_diff_populates_changed_fields_and_versions() -> None:
    old = _base_contract()
    new_ccm = copy.deepcopy(old.ccm)
    new_ccm.version = "2.0.0"
    score_field = next(f for f in new_ccm.contract_schema.fields if f.name == "customer_id")
    score_field.constraints.max_length = 10
    new = DataContract.from_ccm(new_ccm)

    diff = old.diff(new)
    assert diff.source_version == "1.0.0"
    assert diff.target_version == "2.0.0"
    assert any(change.field == "customer_id" for change in diff.changed_fields)
