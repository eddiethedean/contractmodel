"""Tests for nested JSON Schema export."""

from contractmodel.core.ccm import CanonicalContract
from contractmodel.export.json_schema import export_json_schema


def test_nested_object_array_map_schema() -> None:
    contract = CanonicalContract.model_validate(
        {
            "contract_id": "nested",
            "name": "Nested",
            "version": "1.0.0",
            "schema": {
                "fields": [
                    {
                        "name": "profile",
                        "logical_type": "object",
                        "required": True,
                        "children": [
                            {"name": "name", "logical_type": "string", "required": True},
                            {"name": "age", "logical_type": "integer", "nullable": True},
                        ],
                    },
                    {
                        "name": "tags",
                        "logical_type": "array",
                        "children": [{"name": "item", "logical_type": "string"}],
                    },
                    {
                        "name": "metadata",
                        "logical_type": "map",
                        "children": [{"name": "value", "logical_type": "string"}],
                    },
                    {
                        "name": "score",
                        "logical_type": "integer",
                        "nullable": True,
                        "constraints": {
                            "min_value": 0,
                            "max_value": 100,
                            "min_length": 1,
                            "max_length": 3,
                            "pattern": "^[0-9]+$",
                            "enum_values": ["1", "2"],
                        },
                    },
                ],
            },
        }
    )
    schema = export_json_schema(contract)
    props = schema["properties"]
    assert props["profile"]["type"] == "object"
    assert "name" in props["profile"]["required"]
    assert props["tags"]["type"] == "array"
    assert props["metadata"]["additionalProperties"]["type"] == "string"
    assert props["score"]["type"] == ["integer", "null"]
    assert props["score"]["minimum"] == 0
    assert props["score"]["enum"] == ["1", "2"]
