"""Export utilities."""

from __future__ import annotations

from typing import Any

from contractmodel.core.ccm import CanonicalContract


def export_markdown(contract: CanonicalContract) -> str:
    """Export a contract as a minimal Markdown document."""
    lines = [
        f"# {contract.name}",
        "",
        f"- **ID**: {contract.contract_id}",
        f"- **Version**: {contract.version}",
        f"- **Kind**: {contract.kind.value}",
        f"- **Status**: {contract.status.value}",
        "",
    ]
    if contract.description:
        lines.extend([contract.description, ""])

    lines.append("## Schema")
    lines.append("")
    lines.append("| Field | Type | Required | Nullable | Description |")
    lines.append("| --- | --- | --- | --- | --- |")
    for field in contract.schema.fields:
        lines.append(
            f"| {field.name} | {field.logical_type.value} | {field.required} | "
            f"{field.nullable} | {field.description or ''} |"
        )

    return "\n".join(lines) + "\n"


def export_json_schema(contract: CanonicalContract) -> dict[str, Any]:
    """Export a contract as a minimal JSON Schema."""
    properties: dict[str, Any] = {}
    required: list[str] = []

    for field in contract.schema.fields:
        prop: dict[str, Any] = {"type": _logical_type_to_json_schema_type(field.logical_type.value)}
        if field.description:
            prop["description"] = field.description
        if field.constraints.enum_values:
            prop["enum"] = field.constraints.enum_values
        properties[field.name] = prop
        if field.required:
            required.append(field.name)

    schema: dict[str, Any] = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": contract.name,
        "type": "object",
        "properties": properties,
    }
    if required:
        schema["required"] = required
    return schema


def _logical_type_to_json_schema_type(logical_type: str) -> str:
    mapping = {
        "string": "string",
        "integer": "integer",
        "number": "number",
        "decimal": "number",
        "boolean": "boolean",
        "date": "string",
        "time": "string",
        "datetime": "string",
        "uuid": "string",
        "email": "string",
        "uri": "string",
        "enum": "string",
        "array": "array",
        "object": "object",
        "map": "object",
        "binary": "string",
        "any": "string",
    }
    return mapping.get(logical_type, "string")
