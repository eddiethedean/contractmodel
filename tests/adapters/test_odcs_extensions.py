"""Tests for ODCS extensions and metadata round-trip."""


from contractmodel.adapters.odcs import export_odcs, import_odcs


def test_api_version_roundtrip() -> None:
    data = {
        "apiVersion": "v3.1.0",
        "kind": "DataContract",
        "id": "x",
        "name": "X",
        "version": "1.0.0",
        "status": "active",
        "schema": [{"name": "id", "logicalType": "string", "required": True}],
        "customMeta": "preserved",
    }
    contract = import_odcs(data)
    exported = export_odcs(contract)
    assert exported["apiVersion"] == "v3.1.0"
    assert exported["status"] == "active"
    assert exported["customMeta"] == "preserved"


def test_constraint_roundtrip() -> None:
    data = {
        "apiVersion": "v3.0.0",
        "kind": "DataContract",
        "id": "x",
        "name": "X",
        "version": "1.0.0",
        "schema": [
            {
                "name": "score",
                "logicalType": "integer",
                "required": True,
                "minValue": 0,
                "maxValue": 100,
                "unique": True,
            }
        ],
    }
    contract = import_odcs(data)
    field = contract.contract_schema.fields[0]
    assert field.constraints.min_value == 0
    assert field.constraints.max_value == 100
    assert field.constraints.unique is True
    exported = export_odcs(contract)
    exported_field = exported["schema"][0]
    assert exported_field["minValue"] == 0
    assert exported_field["unique"] is True


def test_field_extensions_preserved() -> None:
    data = {
        "apiVersion": "v3.0.0",
        "kind": "DataContract",
        "id": "x",
        "name": "X",
        "version": "1.0.0",
        "schema": [
            {
                "name": "id",
                "logicalType": "string",
                "required": True,
                "vendorTag": "keep-me",
            }
        ],
    }
    contract = import_odcs(data)
    assert contract.contract_schema.fields[0].extensions["vendorTag"] == "keep-me"
    exported = export_odcs(contract)
    assert exported["schema"][0]["vendorTag"] == "keep-me"
