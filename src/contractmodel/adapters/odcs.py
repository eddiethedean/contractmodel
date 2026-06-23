"""ODCS import and export adapter."""

from __future__ import annotations

from typing import Any

from contractmodel.core.ccm import (
    CanonicalContract,
    Contact,
    ContractField,
    ContractSchema,
    Ownership,
)
from contractmodel.core.constraints import FieldConstraints
from contractmodel.core.types import ContractStatus, LogicalType

_ODCS_TOP_LEVEL_KEYS = frozenset(
    {
        "apiVersion",
        "kind",
        "id",
        "name",
        "version",
        "description",
        "owner",
        "schema",
        "status",
    }
)

_ODCS_FIELD_KEYS = frozenset(
    {
        "name",
        "logicalType",
        "logical_type",
        "required",
        "nullable",
        "description",
        "enum",
        "default",
        "examples",
        "aliases",
    }
)


def is_odcs_document(data: dict[str, Any]) -> bool:
    """Return True when the document looks like ODCS."""
    return data.get("kind") == "DataContract" or (
        "apiVersion" in data and "contract_id" not in data
    )


def import_odcs(data: dict[str, Any]) -> CanonicalContract:
    """Convert an ODCS document dict into a CanonicalContract."""
    extensions: dict[str, Any] = {
        k: v for k, v in data.items() if k not in _ODCS_TOP_LEVEL_KEYS
    }

    ownership = _import_ownership(data.get("owner"))
    schema = _import_schema(data.get("schema", []))

    status_raw = data.get("status", "draft")
    status = ContractStatus(str(status_raw).lower())

    return CanonicalContract(
        contract_id=data["id"],
        name=data["name"],
        version=data["version"],
        description=data.get("description"),
        status=status,
        ownership=ownership,
        schema=schema,
        extensions=extensions,
    )


def export_odcs(contract: CanonicalContract) -> dict[str, Any]:
    """Convert a CanonicalContract into an ODCS document dict."""
    result: dict[str, Any] = {
        "apiVersion": contract.extensions.get("apiVersion", "v3.0.0"),
        "kind": contract.extensions.get("kind", "DataContract"),
        "id": contract.contract_id,
        "name": contract.name,
        "version": contract.version,
    }

    if contract.description is not None:
        result["description"] = contract.description

    if contract.ownership is not None:
        result["owner"] = _export_ownership(contract.ownership)

    result["schema"] = [_export_field(field) for field in contract.schema.fields]

    for key, value in contract.extensions.items():
        if key not in {"apiVersion", "kind"}:
            result[key] = value

    return result


def _import_ownership(owner_data: Any) -> Ownership | None:
    if not isinstance(owner_data, dict):
        return None

    contacts: list[Contact] = []
    contact = owner_data.get("contact")
    if contact:
        contacts.append(Contact(email=str(contact)))

    return Ownership(
        owner=owner_data.get("owner"),
        team=owner_data.get("team"),
        contacts=contacts,
    )


def _export_ownership(ownership: Ownership) -> dict[str, Any]:
    result: dict[str, Any] = {}
    if ownership.team:
        result["team"] = ownership.team
    if ownership.owner:
        result["owner"] = ownership.owner
    if ownership.contacts:
        first = ownership.contacts[0]
        if first.email:
            result["contact"] = first.email
    return result


def _import_schema(schema_data: Any) -> ContractSchema:
    if not isinstance(schema_data, list):
        msg = "ODCS schema must be a list of fields"
        raise ValueError(msg)

    return ContractSchema(fields=[_import_field(item) for item in schema_data])


def _import_field(field_data: dict[str, Any]) -> ContractField:
    extensions = {k: v for k, v in field_data.items() if k not in _ODCS_FIELD_KEYS}

    logical_type_raw = field_data.get("logicalType") or field_data.get("logical_type", "string")
    enum_values = field_data.get("enum")

    if enum_values:
        logical_type = LogicalType.ENUM
        constraints = FieldConstraints(enum_values=list(enum_values))
    else:
        logical_type = LogicalType(str(logical_type_raw).lower())
        constraints = FieldConstraints()

    return ContractField(
        name=field_data["name"],
        logical_type=logical_type,
        required=field_data.get("required", True),
        nullable=field_data.get("nullable", False),
        description=field_data.get("description"),
        aliases=field_data.get("aliases", []),
        default=field_data.get("default"),
        examples=field_data.get("examples", []),
        constraints=constraints,
        extensions=extensions,
    )


def _export_field(field: ContractField) -> dict[str, Any]:
    result: dict[str, Any] = {
        "name": field.name,
        "required": field.required,
    }

    if field.logical_type == LogicalType.ENUM and field.constraints.enum_values:
        result["logicalType"] = "string"
        result["enum"] = field.constraints.enum_values
    else:
        result["logicalType"] = field.logical_type.value

    if field.description is not None:
        result["description"] = field.description
    if field.nullable:
        result["nullable"] = field.nullable
    if field.default is not None:
        result["default"] = field.default
    if field.examples:
        result["examples"] = field.examples
    if field.aliases:
        result["aliases"] = field.aliases

    result.update(field.extensions)
    return result
