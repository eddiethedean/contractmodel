"""Tests for ODCS round-trip."""

from pathlib import Path

import yaml

from contractmodel.adapters.odcs import export_odcs, import_odcs
from contractmodel.core.types import LogicalType

EXAMPLES_DIR = Path(__file__).resolve().parents[2] / "examples"


def test_odcs_roundtrip_preserves_identity() -> None:
    path = EXAMPLES_DIR / "customer_events.odcs.yaml"
    with path.open() as f:
        original = yaml.safe_load(f)

    contract = import_odcs(original)
    exported = export_odcs(contract)
    roundtripped = import_odcs(exported)

    assert roundtripped == contract
    assert roundtripped.ownership == contract.ownership
    assert roundtripped.status == contract.status
    assert roundtripped.extensions == contract.extensions

    for original_field, roundtripped_field in zip(
        contract.contract_schema.fields,
        roundtripped.contract_schema.fields,
        strict=True,
    ):
        assert roundtripped_field.name == original_field.name
        assert roundtripped_field.logical_type == original_field.logical_type
        assert roundtripped_field.required == original_field.required
        assert roundtripped_field.nullable == original_field.nullable
        assert roundtripped_field.description == original_field.description
        assert roundtripped_field.constraints == original_field.constraints


def test_odcs_roundtrip_preserves_rich_metadata() -> None:
    data = {
        "apiVersion": "v3.0.0",
        "kind": "DataContract",
        "id": "rich",
        "name": "Rich",
        "version": "1.0.0",
        "status": "active",
        "schema": [
            {
                "name": "label",
                "logicalType": "string",
                "required": False,
                "nullable": True,
                "default": "default",
                "examples": ["a"],
                "aliases": ["identifier"],
                "pattern": "^a",
                "minLength": 1,
                "maxLength": 10,
            }
        ],
        "customMeta": "preserved",
    }
    once = import_odcs(data)
    twice = import_odcs(export_odcs(once))
    assert twice == once
    field = twice.contract_schema.fields[0]
    assert field.default == "default"
    assert field.examples == ["a"]
    assert field.aliases == ["identifier"]
    assert field.constraints.pattern == "^a"
    assert field.constraints.min_length == 1
    assert field.constraints.max_length == 10


def test_odcs_enum_field_roundtrip() -> None:
    path = EXAMPLES_DIR / "customer_events.odcs.yaml"
    with path.open() as f:
        data = yaml.safe_load(f)

    contract = import_odcs(data)
    exported = export_odcs(contract)
    event_type = next(item for item in exported["schema"] if item["name"] == "event_type")

    assert event_type["enum"] == ["created", "updated", "deleted"]

    roundtripped = import_odcs(exported)
    field = next(f for f in roundtripped.contract_schema.fields if f.name == "event_type")
    assert field.logical_type == LogicalType.ENUM
    assert field.constraints.enum_values == ["created", "updated", "deleted"]
