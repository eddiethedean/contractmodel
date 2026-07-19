"""Tests for ODCS extensions and metadata round-trip."""

from contractmodel.adapters.odcs import export_odcs, import_odcs
from contractmodel.adapters.odcs_conformance import validate_odcs_document


def test_api_version_roundtrip() -> None:
    data = {
        "apiVersion": "v3.1.0",
        "kind": "DataContract",
        "id": "x",
        "name": "X",
        "version": "1.0.0",
        "status": "active",
        "domain": "analytics",
        "schema": [
            {
                "name": "row",
                "logicalType": "object",
                "properties": [{"name": "id", "logicalType": "string", "required": True}],
            }
        ],
        "customProperties": [{"property": "customMeta", "value": "preserved"}],
    }
    validate_odcs_document(data)
    contract = import_odcs(data)
    exported = export_odcs(contract)
    assert exported["apiVersion"] == "v3.1.0"
    assert exported["status"] == "active"
    assert exported["domain"] == "analytics"
    assert any(
        item.get("property") == "customMeta" and item.get("value") == "preserved"
        for item in exported.get("customProperties", [])
    )


def test_constraint_roundtrip() -> None:
    data = {
        "apiVersion": "v3.1.0",
        "kind": "DataContract",
        "id": "x",
        "name": "X",
        "version": "1.0.0",
        "status": "draft",
        "schema": [
            {
                "name": "row",
                "logicalType": "object",
                "properties": [
                    {
                        "name": "score",
                        "logicalType": "integer",
                        "required": True,
                        "unique": True,
                        "logicalTypeOptions": {"minimum": 0, "maximum": 100},
                    }
                ],
            }
        ],
    }
    validate_odcs_document(data)
    contract = import_odcs(data)
    field = contract.contract_schema.fields[0]
    assert field.constraints.min_value == 0
    assert field.constraints.max_value == 100
    assert field.constraints.unique is True
    exported = export_odcs(contract)
    exported_field = exported["schema"][0]["properties"][0]
    assert exported_field["logicalTypeOptions"]["minimum"] == 0
    assert exported_field["unique"] is True
    roundtripped = import_odcs(exported)
    assert roundtripped.contract_schema.fields[0].constraints == field.constraints


def test_field_extensions_preserved() -> None:
    data = {
        "apiVersion": "v3.1.0",
        "kind": "DataContract",
        "id": "x",
        "name": "X",
        "version": "1.0.0",
        "status": "draft",
        "schema": [
            {
                "name": "row",
                "logicalType": "object",
                "properties": [
                    {
                        "name": "id",
                        "logicalType": "string",
                        "required": True,
                        "businessName": "Identifier",
                        "customProperties": [{"property": "vendorTag", "value": "keep-me"}],
                    }
                ],
            }
        ],
    }
    validate_odcs_document(data)
    contract = import_odcs(data)
    assert contract.contract_schema.fields[0].extensions["vendorTag"] == "keep-me"
    exported = export_odcs(contract)
    field = exported["schema"][0]["properties"][0]
    assert field["businessName"] == "Identifier"
    assert any(
        item.get("property") == "vendorTag" and item.get("value") == "keep-me"
        for item in field.get("customProperties", [])
    )
