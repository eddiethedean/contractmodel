"""Markdown export."""

from __future__ import annotations

from contractmodel.core.ccm import CanonicalContract, ContractField


def export_markdown(contract: CanonicalContract) -> str:
    """Export a contract as Markdown."""
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

    if contract.ownership:
        lines.append("## Ownership")
        lines.append("")
        if contract.ownership.owner:
            lines.append(f"- **Owner**: {contract.ownership.owner}")
        if contract.ownership.team:
            lines.append(f"- **Team**: {contract.ownership.team}")
        lines.append("")

    if contract.contract_schema.primary_key:
        lines.append(f"**Primary key**: {', '.join(contract.contract_schema.primary_key)}")
        lines.append("")

    lines.extend(["## Schema", "", _fields_table(contract.contract_schema.fields)])

    if contract.quality and contract.quality.rules:
        lines.extend(["", "## Quality Rules", ""])
        for rule in contract.quality.rules:
            lines.append(f"- **{rule.name}** ({rule.type})")

    if contract.semantics and contract.semantics.namespaces:
        lines.extend(["", "## Semantic Namespaces", ""])
        for prefix, uri in contract.semantics.namespaces.items():
            lines.append(f"- `{prefix}` → {uri}")

    return "\n".join(lines) + "\n"


def _fields_table(fields: list[ContractField], indent: int = 0) -> str:
    prefix = "  " * indent
    lines = [
        f"{prefix}| Field | Type | Required | Nullable | Description |",
        f"{prefix}| --- | --- | --- | --- | --- |",
    ]
    for field in fields:
        lines.append(
            f"{prefix}| {_escape_cell(field.name)} | {field.logical_type.value} | "
            f"{field.required} | {field.nullable} | {_escape_cell(field.description or '')} |"
        )
        constraint_summary = _constraint_summary(field)
        if constraint_summary:
            lines.append(f"{prefix}| | | | | _{constraint_summary}_ |")
        if field.children:
            lines.append(f"{prefix}| **{field.name} children** | | | | |")
            lines.append(_fields_table(field.children, indent + 1))
    return "\n".join(lines)


def _constraint_summary(field: ContractField) -> str:
    parts: list[str] = []
    c = field.constraints
    if c.enum_values:
        parts.append(f"enum: {c.enum_values}")
    if c.min_value is not None:
        parts.append(f"min: {c.min_value}")
    if c.max_value is not None:
        parts.append(f"max: {c.max_value}")
    if c.pattern:
        parts.append(f"pattern: {c.pattern}")
    if c.unique:
        parts.append("unique")
    return ", ".join(parts)


def _escape_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")
