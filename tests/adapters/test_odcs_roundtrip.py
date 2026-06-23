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

    assert roundtripped.contract_id == contract.contract_id
    assert roundtripped.name == contract.name
    assert roundtripped.version == contract.version
    assert roundtripped.description == contract.description

    for original_field, roundtripped_field in zip(
        contract.schema.fields,
        roundtripped.schema.fields,
        strict=True,
    ):
        assert original_field.name == roundtripped_field.name
        assert original_field.logical_type == roundtripped_field.logical_type
        assert original_field.required == roundtripped_field.required
        assert original_field.nullable == roundtripped_field.nullable
        assert original_field.description == roundtripped_field.description


def test_odcs_enum_field_roundtrip() -> None:
    path = EXAMPLES_DIR / "customer_events.odcs.yaml"
    with path.open() as f:
        data = yaml.safe_load(f)

    contract = import_odcs(data)
    exported = export_odcs(contract)
    event_type = next(item for item in exported["schema"] if item["name"] == "event_type")

    assert event_type["enum"] == ["created", "updated", "deleted"]

    roundtripped = import_odcs(exported)
    field = next(f for f in roundtripped.schema.fields if f.name == "event_type")
    assert field.logical_type == LogicalType.ENUM
