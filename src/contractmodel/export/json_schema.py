"""JSON Schema export."""

from __future__ import annotations

from typing import Any

from contractmodel.core.ccm import CanonicalContract, ContractField
from contractmodel.core.types import LogicalType


def export_json_schema(contract: CanonicalContract) -> dict[str, Any]:
    """Export a contract as JSON Schema draft 2020-12."""
    properties = {field.name: _field_to_schema(field) for field in contract.contract_schema.fields}
    required = [
        field.name for field in contract.contract_schema.fields if field.required and not field.nullable
    ]

    schema: dict[str, Any] = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": contract.name,
        "type": "object",
        "properties": properties,
    }
    if required:
        schema["required"] = required
    return schema


def _field_to_schema(field: ContractField) -> dict[str, Any]:
    prop: dict[str, Any] = {}

    if field.logical_type == LogicalType.OBJECT:
        prop["type"] = "object"
        if field.children:
            prop["properties"] = {child.name: _field_to_schema(child) for child in field.children}
            child_required = [
                child.name for child in field.children if child.required and not child.nullable
            ]
            if child_required:
                prop["required"] = child_required
    elif field.logical_type == LogicalType.ARRAY:
        prop["type"] = "array"
        if field.children:
            prop["items"] = _field_to_schema(field.children[0])
    elif field.logical_type == LogicalType.MAP:
        prop["type"] = "object"
        if field.children:
            prop["additionalProperties"] = _field_to_schema(field.children[0])
    else:
        json_type, fmt = _logical_type_to_json_schema(field.logical_type)
        if field.nullable:
            prop["type"] = [json_type, "null"]
        else:
            prop["type"] = json_type
        if fmt:
            prop["format"] = fmt

    if field.description:
        prop["description"] = field.description
    constraints = field.constraints
    if constraints.enum_values:
        prop["enum"] = constraints.enum_values
    if constraints.min_length is not None:
        prop["minLength"] = constraints.min_length
    if constraints.max_length is not None:
        prop["maxLength"] = constraints.max_length
    if constraints.min_value is not None:
        prop["minimum"] = constraints.min_value
    if constraints.max_value is not None:
        prop["maximum"] = constraints.max_value
    if constraints.pattern is not None:
        prop["pattern"] = constraints.pattern

    return prop


def _logical_type_to_json_schema(logical_type: LogicalType) -> tuple[str, str | None]:
    mapping: dict[LogicalType, tuple[str, str | None]] = {
        LogicalType.STRING: ("string", None),
        LogicalType.INTEGER: ("integer", None),
        LogicalType.NUMBER: ("number", None),
        LogicalType.DECIMAL: ("number", None),
        LogicalType.BOOLEAN: ("boolean", None),
        LogicalType.DATE: ("string", "date"),
        LogicalType.TIME: ("string", "time"),
        LogicalType.DATETIME: ("string", "date-time"),
        LogicalType.DURATION: ("string", "duration"),
        LogicalType.UUID: ("string", "uuid"),
        LogicalType.EMAIL: ("string", "email"),
        LogicalType.URI: ("string", "uri"),
        LogicalType.ENUM: ("string", None),
        LogicalType.ARRAY: ("array", None),
        LogicalType.OBJECT: ("object", None),
        LogicalType.MAP: ("object", None),
        LogicalType.BINARY: ("string", None),
        LogicalType.ANY: ("string", None),
    }
    return mapping.get(logical_type, ("string", None))
