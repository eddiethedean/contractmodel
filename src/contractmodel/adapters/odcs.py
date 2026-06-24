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
from contractmodel.errors import OdcsImportError

_ODCS_TOP_LEVEL_KEYS = frozenset(
    {
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
        "minValue",
        "maxValue",
        "minLength",
        "maxLength",
        "pattern",
        "unique",
        "min_value",
        "max_value",
        "min_length",
        "max_length",
    }
)

_ODCS_FIELD_RESERVED = frozenset(
    {
        "name",
        "logicalType",
        "required",
        "nullable",
        "description",
        "enum",
        "default",
        "examples",
        "aliases",
        "minValue",
        "maxValue",
        "minLength",
        "maxLength",
        "pattern",
        "unique",
    }
)


def is_odcs_document(data: dict[str, Any]) -> bool:
    """Return True when the document looks like ODCS."""
    if data.get("format") == "odcs":
        return True
    if "contract_id" in data:
        return False
    if isinstance(data.get("schema"), list) and "id" in data:
        if "apiVersion" in data:
            return True
        if data.get("kind") == "DataContract":
            return True
    return False


def import_odcs(data: dict[str, Any]) -> CanonicalContract:
    """Convert an ODCS document dict into a CanonicalContract."""
    _validate_required_keys(data, ["id", "name", "version"])

    extensions: dict[str, Any] = {
        k: v for k, v in data.items() if k not in _ODCS_TOP_LEVEL_KEYS
    }
    if "apiVersion" in data:
        extensions.setdefault("apiVersion", data["apiVersion"])
    if "kind" in data:
        extensions.setdefault("kind", data["kind"])

    ownership = _import_ownership(data.get("owner"))
    schema = _import_schema(data.get("schema", []))

    status_raw = data.get("status", "draft")
    try:
        status = ContractStatus(str(status_raw).lower())
    except ValueError as exc:
        msg = f"Invalid contract status: {status_raw}"
        raise OdcsImportError(msg) from exc

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
    result: dict[str, Any] = dict(contract.extensions)

    result["apiVersion"] = result.get("apiVersion", "v3.0.0")
    result["kind"] = result.get("kind", "DataContract")
    result["id"] = contract.contract_id
    result["name"] = contract.name
    result["version"] = contract.version
    result["status"] = contract.status.value

    if contract.description is not None:
        result["description"] = contract.description

    if contract.ownership is not None:
        result["owner"] = _export_ownership(contract.ownership)

    result["schema"] = [_export_field(field) for field in contract.contract_schema.fields]

    return result


def _validate_required_keys(data: dict[str, Any], keys: list[str]) -> None:
    missing = [key for key in keys if key not in data]
    if missing:
        msg = f"ODCS document missing required keys: {', '.join(missing)}"
        raise OdcsImportError(msg)


def _import_ownership(owner_data: Any) -> Ownership | None:
    if not isinstance(owner_data, dict):
        return None

    contacts: list[Contact] = []
    contact = owner_data.get("contact")
    if contact:
        contacts.extend(_parse_contacts(contact))

    return Ownership(
        owner=owner_data.get("owner"),
        team=owner_data.get("team"),
        contacts=contacts,
    )


def _parse_contacts(contact: Any) -> list[Contact]:
    if isinstance(contact, list):
        return [_contact_from_item(item) for item in contact]
    return [_contact_from_item(contact)]


def _contact_from_item(item: Any) -> Contact:
    if isinstance(item, dict):
        return Contact(
            email=item.get("email"),
            name=item.get("name"),
            role=item.get("role"),
        )
    return Contact(email=str(item))


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
        raise OdcsImportError(msg)

    fields: list[ContractField] = []
    for index, item in enumerate(schema_data):
        if not isinstance(item, dict):
            msg = f"ODCS schema item {index} must be an object"
            raise OdcsImportError(msg)
        fields.append(_import_field(item))
    return ContractSchema(fields=fields)


def _import_field(field_data: dict[str, Any]) -> ContractField:
    if "name" not in field_data:
        msg = "ODCS field is missing required key 'name'"
        raise OdcsImportError(msg)

    extensions = {k: v for k, v in field_data.items() if k not in _ODCS_FIELD_KEYS}

    logical_type_raw = field_data.get("logicalType") or field_data.get("logical_type", "string")
    enum_values = field_data.get("enum")

    if enum_values is not None:
        if not enum_values:
            msg = f"ODCS field '{field_data['name']}' enum must be non-empty"
            raise OdcsImportError(msg)
        logical_type = LogicalType.ENUM
        constraints = _import_constraints(field_data, enum_values=list(enum_values))
    elif str(logical_type_raw).lower() == LogicalType.ENUM.value:
        msg = f"ODCS field '{field_data['name']}' enum type requires enum values"
        raise OdcsImportError(msg)
    else:
        try:
            logical_type = LogicalType(str(logical_type_raw).lower())
        except ValueError as exc:
            msg = f"Invalid logical type: {logical_type_raw}"
            raise OdcsImportError(msg) from exc
        constraints = _import_constraints(field_data)

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


def _import_constraints(
    field_data: dict[str, Any],
    *,
    enum_values: list[Any] | None = None,
) -> FieldConstraints:
    return FieldConstraints(
        min_value=field_data.get("minValue", field_data.get("min_value")),
        max_value=field_data.get("maxValue", field_data.get("max_value")),
        min_length=field_data.get("minLength", field_data.get("min_length")),
        max_length=field_data.get("maxLength", field_data.get("max_length")),
        pattern=field_data.get("pattern"),
        unique=bool(field_data.get("unique", False)),
        enum_values=enum_values,
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

    constraints = field.constraints
    if constraints.min_value is not None:
        result["minValue"] = constraints.min_value
    if constraints.max_value is not None:
        result["maxValue"] = constraints.max_value
    if constraints.min_length is not None:
        result["minLength"] = constraints.min_length
    if constraints.max_length is not None:
        result["maxLength"] = constraints.max_length
    if constraints.pattern is not None:
        result["pattern"] = constraints.pattern
    if constraints.unique:
        result["unique"] = True

    for key, value in field.extensions.items():
        if key not in _ODCS_FIELD_RESERVED:
            result[key] = value

    return result
