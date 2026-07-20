"""ODCS import and export adapter (CCM mapping; conformance via pyodcs)."""

from __future__ import annotations

from typing import Any

from contractmodel.adapters.odcs_conformance import validate_odcs_document
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
from contractmodel.extensions import validate_extensions
from contractmodel.versions import DEFAULT_ODCS_API_VERSION, normalize_odcs_api_version

# Keys mapped into CCM fields (not stored as opaque extensions).
_ODCS_MAPPED_TOP_LEVEL = frozenset(
    {
        "id",
        "name",
        "version",
        "description",
        "team",
        "support",
        "schema",
        "status",
        "owner",  # legacy; rejected by pyodcs but ignored if somehow present
    }
)

_ODCS_FIELD_KEYS = frozenset(
    {
        "name",
        "logicalType",
        "logical_type",
        "logicalTypeOptions",
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
        "properties",
        "items",
        "children",
        "customProperties",
    }
)

_ODCS_FIELD_RESERVED = frozenset(
    {
        "name",
        "logicalType",
        "logicalTypeOptions",
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
        "properties",
        "items",
        "customProperties",
    }
)

_CCM_TO_ODCS_TYPE: dict[LogicalType, str] = {
    LogicalType.STRING: "string",
    LogicalType.INTEGER: "integer",
    LogicalType.NUMBER: "number",
    LogicalType.DECIMAL: "number",
    LogicalType.BOOLEAN: "boolean",
    LogicalType.DATE: "date",
    LogicalType.TIME: "time",
    LogicalType.DATETIME: "timestamp",
    LogicalType.DURATION: "string",
    LogicalType.ARRAY: "array",
    LogicalType.OBJECT: "object",
    LogicalType.MAP: "object",
    LogicalType.BINARY: "string",
    LogicalType.UUID: "string",
    LogicalType.URI: "string",
    LogicalType.EMAIL: "string",
    LogicalType.ENUM: "string",
    LogicalType.ANY: "string",
}

_STRING_FORMAT_TYPES = {
    "uuid": LogicalType.UUID,
    "uri": LogicalType.URI,
    "email": LogicalType.EMAIL,
    "binary": LogicalType.BINARY,
}

_EXTENSION_SCHEMA_NAME = "odcsSchemaName"
_EXTENSION_SCHEMA_PHYSICAL = "odcsSchemaPhysicalName"
_EXTENSION_TEAM = "odcsTeam"
_EXTENSION_DESCRIPTION = "odcsDescription"
_CCM_TYPE_PROPERTY = "ccmLogicalType"

_ODCS_TOP_LEVEL_PASSTHROUGH = frozenset(
    {
        "apiVersion",
        "kind",
        "tenant",
        "tags",
        "servers",
        "dataProduct",
        "domain",
        "price",
        "roles",
        "slaDefaultElement",
        "slaProperties",
        "authoritativeDefinitions",
        "customProperties",
        "contractCreatedTs",
    }
)

_ODCS_FIELD_PASSTHROUGH = frozenset(
    {
        "businessName",
        "physicalName",
        "physicalType",
        "primaryKey",
        "primaryKeyPosition",
        "classification",
        "criticalDataElement",
        "encryptedName",
        "partitioned",
        "partitionKeyPosition",
        "quality",
        "relationships",
        "authoritativeDefinitions",
        "tags",
    }
)


def _coerce_bool(value: Any, default: bool) -> bool:
    """Coerce ODCS boolean fields from YAML/JSON loose types."""
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, int) and value in (0, 1):
        return bool(value)
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "yes", "1"}:
            return True
        if normalized in {"false", "no", "0"}:
            return False
        msg = f"Invalid boolean value: {value!r}"
        raise OdcsImportError(msg)
    return bool(value)


def is_odcs_document(data: dict[str, Any]) -> bool:
    """Return True when the document looks like ODCS.

    Native CCM documents (``contract_id`` present) always win over ODCS heuristics,
    including a leftover ``format: odcs`` key.
    """
    if "contract_id" in data:
        return False
    if data.get("format") == "odcs":
        return isinstance(data.get("schema"), list) and "id" in data
    if isinstance(data.get("schema"), list) and "id" in data:
        if "apiVersion" in data:
            return True
        if data.get("kind") == "DataContract":
            return True
    return False


def import_odcs(data: dict[str, Any]) -> CanonicalContract:
    """Convert a pyodcs-validated ODCS document dict into a CanonicalContract."""
    api_version = normalize_odcs_api_version(
        data.get("apiVersion") if isinstance(data.get("apiVersion"), str) else None
    )

    extensions: dict[str, Any] = {
        key: value for key, value in data.items() if key not in _ODCS_MAPPED_TOP_LEVEL
    }
    if api_version is not None:
        extensions.setdefault("apiVersion", api_version)
    if "kind" in data:
        extensions.setdefault("kind", data["kind"])
    if isinstance(data.get("team"), dict):
        extensions.setdefault(_EXTENSION_TEAM, data["team"])
    if isinstance(data.get("description"), dict):
        extensions.setdefault(_EXTENSION_DESCRIPTION, data["description"])

    schema, schema_extensions = _import_schema(data.get("schema", []))
    extensions.update(schema_extensions)
    validate_extensions(extensions, path="extensions")

    ownership = _import_ownership(data)
    description = _import_description(data.get("description"))

    status_raw = data.get("status", "draft")
    try:
        status = ContractStatus(str(status_raw).lower())
    except ValueError as exc:
        msg = f"Invalid contract status: {status_raw}"
        raise OdcsImportError(msg) from exc

    return CanonicalContract(
        contract_id=str(data["id"]),
        name=str(data["name"]),
        version=str(data["version"]),
        description=description,
        status=status,
        ownership=ownership,
        schema=schema,
        extensions=extensions,
    )


def collect_odcs_import_warnings(data: dict[str, Any]) -> list[str]:
    """Return human-readable lossy-import messages for an ODCS document."""
    messages: list[str] = []
    team = data.get("team")
    if isinstance(team, list):
        messages.append("ODCS team member list mapped to ownership contacts")
    elif isinstance(team, dict) and isinstance(team.get("members"), list) and team["members"]:
        messages.append("ODCS team.members preserved in extensions; contacts also mapped")

    support = data.get("support")
    if isinstance(support, list):
        for item in support:
            if not isinstance(item, dict):
                messages.append("ODCS support entries that are not mailto were skipped")
                break
            url = item.get("url")
            if not (isinstance(url, str) and url.startswith("mailto:")):
                messages.append("ODCS support entries that are not mailto were skipped")
                break

    description = data.get("description")
    if isinstance(description, dict):
        parts = [
            key
            for key in ("purpose", "usage", "limitations")
            if isinstance(description.get(key), str) and str(description.get(key)).strip()
        ]
        if len(parts) > 1:
            messages.append(
                "ODCS description keeps purpose/usage/limitations in extensions; "
                "CCM description uses the first non-empty part"
            )
    return messages


def export_odcs(contract: CanonicalContract, *, validate: bool = True) -> dict[str, Any]:
    """Convert a CanonicalContract into a pyodcs-valid ODCS document dict."""
    result: dict[str, Any] = {}
    extra_custom: list[dict[str, Any]] = []
    existing_custom = contract.extensions.get("customProperties")
    if isinstance(existing_custom, list):
        extra_custom.extend(item for item in existing_custom if isinstance(item, dict))

    skip_extension_keys = {
        _EXTENSION_SCHEMA_NAME,
        _EXTENSION_SCHEMA_PHYSICAL,
        _EXTENSION_TEAM,
        _EXTENSION_DESCRIPTION,
        "format",
        "owner",
        "customProperties",
    }
    for key, value in contract.extensions.items():
        if key in skip_extension_keys:
            continue
        if key in _ODCS_TOP_LEVEL_PASSTHROUGH:
            result[key] = value
        else:
            extra_custom.append({"property": key, "value": value})

    result["apiVersion"] = result.get("apiVersion", DEFAULT_ODCS_API_VERSION)
    result["kind"] = result.get("kind", "DataContract")
    result["id"] = contract.contract_id
    result["name"] = contract.name
    result["version"] = contract.version
    result["status"] = contract.status.value

    stored_description = contract.extensions.get(_EXTENSION_DESCRIPTION)
    if isinstance(stored_description, dict):
        result["description"] = stored_description
    elif contract.description is not None:
        result["description"] = {"purpose": contract.description}

    stored_team = contract.extensions.get(_EXTENSION_TEAM)
    if isinstance(stored_team, dict):
        team_doc = dict(stored_team)
        if contract.ownership is not None and contract.ownership.team:
            team_doc["name"] = contract.ownership.team
        result["team"] = team_doc
    else:
        exported_team = _export_team(contract.ownership)
        if exported_team is not None:
            result["team"] = exported_team

    support = _export_support(contract.ownership)
    if support is not None:
        result["support"] = support

    if extra_custom:
        result["customProperties"] = extra_custom

    schema_name = str(
        contract.extensions.get(_EXTENSION_SCHEMA_NAME)
        or contract.contract_id.replace("-", "_")
    )
    properties = [_export_field(field) for field in contract.contract_schema.fields]
    for field in contract.contract_schema.fields:
        if field.name in contract.contract_schema.primary_key:
            for prop in properties:
                if prop.get("name") == field.name:
                    prop["primaryKey"] = True
    schema_object: dict[str, Any] = {
        "name": schema_name,
        "logicalType": "object",
        "properties": properties,
    }
    physical = contract.extensions.get(_EXTENSION_SCHEMA_PHYSICAL)
    if isinstance(physical, str) and physical:
        schema_object["physicalName"] = physical
    result["schema"] = [schema_object]

    if validate:
        validate_odcs_document(result)
    return result


def _import_description(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        for key in ("purpose", "usage", "limitations"):
            part = value.get(key)
            if isinstance(part, str) and part.strip():
                return part
    return None


def _import_ownership(data: dict[str, Any]) -> Ownership | None:
    team_data = data.get("team")
    support = data.get("support")
    legacy_owner = data.get("owner")

    team_name: str | None = None
    contacts: list[Contact] = []

    if isinstance(team_data, dict):
        name = team_data.get("name")
        if isinstance(name, str) and name:
            team_name = name
        members = team_data.get("members")
        if isinstance(members, list):
            for member in members:
                if not isinstance(member, dict):
                    continue
                contacts.append(
                    Contact(
                        name=member.get("name") or member.get("username"),
                        role=member.get("role"),
                        email=None,
                    )
                )
    elif isinstance(team_data, list):
        for member in team_data:
            if not isinstance(member, dict):
                continue
            contacts.append(
                Contact(
                    name=member.get("name") or member.get("username"),
                    role=member.get("role"),
                    email=None,
                )
            )

    if isinstance(support, list):
        for item in support:
            if not isinstance(item, dict):
                continue
            url = item.get("url")
            if isinstance(url, str) and url.startswith("mailto:"):
                contacts.append(Contact(email=url.removeprefix("mailto:")))

    if isinstance(legacy_owner, dict):
        if team_name is None and isinstance(legacy_owner.get("team"), str):
            team_name = legacy_owner["team"]
        contact = legacy_owner.get("contact")
        if contact:
            contacts.extend(_parse_contacts(contact))

    if team_name is None and not contacts:
        return None
    return Ownership(team=team_name, contacts=contacts)


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


def _export_team(ownership: Ownership | None) -> dict[str, Any] | None:
    if ownership is None or not ownership.team:
        return None
    return {"name": ownership.team}


def _export_support(ownership: Ownership | None) -> list[dict[str, str]] | None:
    if ownership is None:
        return None
    items: list[dict[str, str]] = []
    for contact in ownership.contacts:
        if contact.email:
            items.append({"channel": "email", "url": f"mailto:{contact.email}"})
    return items or None


def _import_schema(schema_data: Any) -> tuple[ContractSchema, dict[str, Any]]:
    if not isinstance(schema_data, list):
        return ContractSchema(fields=[]), {}

    fields: list[ContractField] = []
    schema_extensions: dict[str, Any] = {}
    primary_key: list[str] = []

    dict_entries = [item for item in schema_data if isinstance(item, dict)]
    object_elements = [
        item
        for item in dict_entries
        if str(item.get("logicalType", "")).lower() == "object"
        and isinstance(item.get("properties"), list)
    ]

    # Flatten only when the document is a single object schema element.
    if len(object_elements) == 1 and len(dict_entries) == 1:
        element = object_elements[0]
        name = element.get("name")
        if isinstance(name, str) and name:
            schema_extensions[_EXTENSION_SCHEMA_NAME] = name
        physical = element.get("physicalName")
        if isinstance(physical, str) and physical:
            schema_extensions[_EXTENSION_SCHEMA_PHYSICAL] = physical
        for prop in element.get("properties") or []:
            if isinstance(prop, dict):
                field = _import_field(prop)
                fields.append(field)
                if prop.get("primaryKey") is True:
                    primary_key.append(field.name)
    else:
        for item in dict_entries:
            field = _import_field(item)
            fields.append(field)
            if item.get("primaryKey") is True:
                primary_key.append(field.name)

    return ContractSchema(fields=fields, primary_key=primary_key), schema_extensions


def _import_children(field_data: dict[str, Any]) -> list[ContractField]:
    properties = field_data.get("properties")
    if isinstance(properties, list):
        return [_import_field(item) for item in properties if isinstance(item, dict)]

    items = field_data.get("items")
    if isinstance(items, dict):
        return [_import_field(items)]
    if isinstance(items, list):
        return [_import_field(item) for item in items if isinstance(item, dict)]

    nested = field_data.get("children")
    if isinstance(nested, list):
        return [_import_field(item) for item in nested if isinstance(item, dict)]

    return []


def _custom_property_map(field_data: dict[str, Any]) -> dict[str, Any]:
    raw = field_data.get("customProperties")
    if not isinstance(raw, list):
        return {}
    result: dict[str, Any] = {}
    for item in raw:
        if isinstance(item, dict) and "property" in item:
            result[str(item["property"])] = item.get("value")
    return result


def _import_field(field_data: dict[str, Any]) -> ContractField:
    name = field_data.get("name")
    if not isinstance(name, str) or not name:
        msg = "ODCS field is missing required key 'name'"
        raise OdcsImportError(msg)

    custom = _custom_property_map(field_data)
    extensions = {k: v for k, v in field_data.items() if k not in _ODCS_FIELD_KEYS}
    for key, value in custom.items():
        if key not in {"enum", "nullable", "default", "aliases", _CCM_TYPE_PROPERTY}:
            extensions.setdefault(key, value)
    validate_extensions(extensions, path=f"fields.{name}.extensions")

    options = field_data.get("logicalTypeOptions")
    if not isinstance(options, dict):
        options = {}

    logical_type_raw = field_data.get("logicalType") or field_data.get("logical_type", "string")
    enum_values = field_data.get("enum")
    if enum_values is None and "enum" in custom:
        enum_values = custom["enum"]
    children = _import_children(field_data)

    if enum_values is not None:
        if not enum_values:
            msg = f"ODCS field '{name}' enum must be non-empty"
            raise OdcsImportError(msg)
        logical_type = LogicalType.ENUM
        constraints = _import_constraints(field_data, options, enum_values=list(enum_values))
    elif str(logical_type_raw).lower() == LogicalType.ENUM.value:
        msg = f"ODCS field '{name}' enum type requires enum values"
        raise OdcsImportError(msg)
    elif custom.get(_CCM_TYPE_PROPERTY) in {
        LogicalType.MAP.value,
        LogicalType.DECIMAL.value,
        LogicalType.DURATION.value,
        LogicalType.ANY.value,
    }:
        logical_type = LogicalType(str(custom[_CCM_TYPE_PROPERTY]))
        constraints = _import_constraints(field_data, options)
    else:
        logical_type = _map_import_logical_type(str(logical_type_raw), options)
        constraints = _import_constraints(field_data, options)

    if logical_type == LogicalType.ARRAY and children:
        children = [
            child.model_copy(update={"name": "item"}) if index == 0 else child
            for index, child in enumerate(children)
        ]
    elif logical_type == LogicalType.MAP and children:
        children = [
            child.model_copy(update={"name": "value"}) if index == 0 else child
            for index, child in enumerate(children)
        ]

    aliases = field_data.get("aliases", custom.get("aliases", []))
    if not isinstance(aliases, list):
        aliases = []

    return ContractField(
        name=name,
        logical_type=logical_type,
        required=_coerce_bool(field_data.get("required"), True),
        nullable=_coerce_bool(field_data.get("nullable", custom.get("nullable")), False),
        description=field_data.get("description")
        if isinstance(field_data.get("description"), str)
        else None,
        aliases=aliases,
        default=field_data.get("default", custom.get("default")),
        examples=(
            field_data.get("examples", [])
            if isinstance(field_data.get("examples"), list)
            else []
        ),
        constraints=constraints,
        children=children,
        extensions=extensions,
    )


def _map_import_logical_type(raw: str, options: dict[str, Any]) -> LogicalType:
    lowered = raw.lower()
    if lowered == "timestamp":
        return LogicalType.DATETIME
    if lowered == "string":
        fmt = options.get("format")
        if isinstance(fmt, str) and fmt.lower() in _STRING_FORMAT_TYPES:
            return _STRING_FORMAT_TYPES[fmt.lower()]
        return LogicalType.STRING
    try:
        return LogicalType(lowered)
    except ValueError as exc:
        msg = f"Invalid logical type: {raw}"
        raise OdcsImportError(msg) from exc


def _import_constraints(
    field_data: dict[str, Any],
    options: dict[str, Any],
    *,
    enum_values: list[Any] | None = None,
) -> FieldConstraints:
    return FieldConstraints(
        min_value=field_data.get("minValue", field_data.get("min_value", options.get("minimum"))),
        max_value=field_data.get("maxValue", field_data.get("max_value", options.get("maximum"))),
        min_length=field_data.get(
            "minLength", field_data.get("min_length", options.get("minLength"))
        ),
        max_length=field_data.get(
            "maxLength", field_data.get("max_length", options.get("maxLength"))
        ),
        pattern=field_data.get("pattern", options.get("pattern")),
        unique=_coerce_bool(field_data.get("unique"), False),
        enum_values=enum_values,
    )


def _export_field(field: ContractField) -> dict[str, Any]:
    result: dict[str, Any] = {
        "name": field.name,
        "required": field.required,
    }

    custom_properties: list[dict[str, Any]] = []
    odcs_type = _CCM_TO_ODCS_TYPE.get(field.logical_type, "string")
    options: dict[str, Any] = {}

    if field.logical_type == LogicalType.ENUM and field.constraints.enum_values:
        result["logicalType"] = "string"
        custom_properties.append(
            {"property": "enum", "value": list(field.constraints.enum_values)}
        )
    elif field.logical_type == LogicalType.UUID:
        result["logicalType"] = "string"
        options["format"] = "uuid"
    elif field.logical_type == LogicalType.EMAIL:
        result["logicalType"] = "string"
        options["format"] = "email"
    elif field.logical_type == LogicalType.URI:
        result["logicalType"] = "string"
        options["format"] = "uri"
    elif field.logical_type == LogicalType.BINARY:
        result["logicalType"] = "string"
        options["format"] = "binary"
    elif field.logical_type == LogicalType.MAP:
        result["logicalType"] = "object"
        custom_properties.append({"property": _CCM_TYPE_PROPERTY, "value": "map"})
    elif field.logical_type in {LogicalType.DECIMAL, LogicalType.DURATION, LogicalType.ANY}:
        result["logicalType"] = _CCM_TO_ODCS_TYPE[field.logical_type]
        custom_properties.append(
            {"property": _CCM_TYPE_PROPERTY, "value": field.logical_type.value}
        )
    else:
        result["logicalType"] = odcs_type

    if field.description is not None:
        result["description"] = field.description
    if field.examples:
        result["examples"] = field.examples
    if field.constraints.unique:
        result["unique"] = True

    constraints = field.constraints
    if constraints.min_length is not None:
        options["minLength"] = constraints.min_length
    if constraints.max_length is not None:
        options["maxLength"] = constraints.max_length
    if constraints.pattern is not None:
        options["pattern"] = constraints.pattern
    if constraints.min_value is not None:
        options["minimum"] = constraints.min_value
    if constraints.max_value is not None:
        options["maximum"] = constraints.max_value

    if options:
        result["logicalTypeOptions"] = options

    if field.nullable:
        custom_properties.append({"property": "nullable", "value": True})
    if field.default is not None:
        custom_properties.append({"property": "default", "value": field.default})
    if field.aliases:
        custom_properties.append({"property": "aliases", "value": field.aliases})

    if field.children:
        if field.logical_type == LogicalType.OBJECT:
            result["properties"] = [_export_field(child) for child in field.children]
        elif field.logical_type == LogicalType.ARRAY:
            if field.children:
                result["items"] = _export_field(field.children[0])
        elif field.logical_type == LogicalType.MAP:
            result["properties"] = [_export_field(child) for child in field.children]
        else:
            result["properties"] = [_export_field(child) for child in field.children]

    for key, value in field.extensions.items():
        if key in _ODCS_FIELD_RESERVED or key == _CCM_TYPE_PROPERTY:
            continue
        if key in _ODCS_FIELD_PASSTHROUGH:
            result[key] = value
        else:
            custom_properties.append({"property": key, "value": value})

    if custom_properties:
        result["customProperties"] = custom_properties

    return result
