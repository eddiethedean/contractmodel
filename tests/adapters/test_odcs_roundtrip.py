"""Tests for ODCS round-trip."""

from pathlib import Path

import yaml

from contractmodel.adapters.odcs import export_odcs, import_odcs
from contractmodel.adapters.odcs_conformance import validate_odcs_document
from contractmodel.core.types import LogicalType

EXAMPLES_DIR = Path(__file__).resolve().parents[2] / "examples"


def test_odcs_roundtrip_preserves_identity() -> None:
    path = EXAMPLES_DIR / "customer_events.odcs.yaml"
    with path.open() as f:
        original = yaml.safe_load(f)

    contract = import_odcs(original)
    exported = export_odcs(contract)
    validate_odcs_document(exported)
    roundtripped = import_odcs(exported)

    assert roundtripped.contract_id == contract.contract_id
    assert roundtripped.name == contract.name
    assert roundtripped.version == contract.version
    assert roundtripped.status == contract.status
    assert roundtripped.ownership is not None
    assert contract.ownership is not None
    assert roundtripped.ownership.team == contract.ownership.team
    assert roundtripped.ownership.contacts[0].email == contract.ownership.contacts[0].email

    for original_field, roundtripped_field in zip(
        contract.contract_schema.fields,
        roundtripped.contract_schema.fields,
        strict=True,
    ):
        assert roundtripped_field.name == original_field.name
        assert roundtripped_field.logical_type == original_field.logical_type
        assert roundtripped_field.required == original_field.required
        assert roundtripped_field.description == original_field.description
        assert roundtripped_field.constraints.enum_values == original_field.constraints.enum_values


def test_odcs_roundtrip_preserves_rich_metadata() -> None:
    data = {
        "apiVersion": "v3.1.0",
        "kind": "DataContract",
        "id": "rich",
        "name": "Rich",
        "version": "1.0.0",
        "status": "active",
        "schema": [
            {
                "name": "rich_row",
                "logicalType": "object",
                "properties": [
                    {
                        "name": "label",
                        "logicalType": "string",
                        "required": False,
                        "logicalTypeOptions": {
                            "pattern": "^a",
                            "minLength": 1,
                            "maxLength": 10,
                        },
                        "examples": ["a"],
                        "customProperties": [
                            {"property": "nullable", "value": True},
                            {"property": "default", "value": "default"},
                            {"property": "aliases", "value": ["identifier"]},
                        ],
                    }
                ],
            }
        ],
        "domain": "analytics",
    }
    validate_odcs_document(data)
    once = import_odcs(data)
    twice = import_odcs(export_odcs(once))
    assert twice.contract_id == once.contract_id
    field = twice.contract_schema.fields[0]
    assert field.default == "default"
    assert field.examples == ["a"]
    assert field.aliases == ["identifier"]
    assert field.constraints.pattern == "^a"
    assert field.constraints.min_length == 1
    assert field.constraints.max_length == 10
    assert twice.extensions.get("domain") == "analytics"


def test_odcs_enum_field_roundtrip() -> None:
    path = EXAMPLES_DIR / "customer_events.odcs.yaml"
    with path.open() as f:
        data = yaml.safe_load(f)

    contract = import_odcs(data)
    exported = export_odcs(contract)
    props = exported["schema"][0]["properties"]
    event_type = next(item for item in props if item["name"] == "event_type")

    enum_prop = next(
        item for item in event_type["customProperties"] if item["property"] == "enum"
    )
    assert enum_prop["value"] == ["created", "updated", "deleted"]

    roundtripped = import_odcs(exported)
    field = next(f for f in roundtripped.contract_schema.fields if f.name == "event_type")
    assert field.logical_type == LogicalType.ENUM
    assert field.constraints.enum_values == ["created", "updated", "deleted"]
