"""Tests for JSON Schema export."""

from contractmodel import DataContract
from contractmodel.export.json_schema import export_json_schema


def test_json_schema_required_and_enum() -> None:
    contract = DataContract.from_odcs("examples/customer_events.odcs.yaml")
    schema = export_json_schema(contract.ccm)
    assert "event_id" in schema["required"]
    event_type = schema["properties"]["event_type"]
    assert "enum" in event_type


def test_json_schema_nested_object() -> None:
    from contractmodel.core.ccm import CanonicalContract

    contract = CanonicalContract.model_validate(
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
    schema = export_json_schema(contract)
    assert "properties" in schema["properties"]["address"]
