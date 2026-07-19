"""Extra coverage for ODCS adapter and pyodcs conformance helpers."""

from __future__ import annotations

from pathlib import Path

import pytest

from contractmodel.adapters.odcs import export_odcs, import_odcs
from contractmodel.adapters.odcs_conformance import (
    _error_diagnostics,
    _raise_if_invalid,
    parse_and_validate_odcs,
    parse_and_validate_odcs_file,
    validate_odcs_document,
)
from contractmodel.core.ccm import CanonicalContract, Ownership
from contractmodel.errors import OdcsImportError, OdcsValidationError

EXAMPLES = Path(__file__).resolve().parents[2] / "examples"


def test_parse_helpers_and_error_diagnostics() -> None:
    path = EXAMPLES / "customer_events.odcs.yaml"
    parsed = parse_and_validate_odcs_file(path)
    assert parsed["id"] == "customer-events"
    text = path.read_text(encoding="utf-8")
    assert parse_and_validate_odcs(text)["id"] == "customer-events"
    assert parse_and_validate_odcs(text.encode())["id"] == "customer-events"
    assert _error_diagnostics({"diagnostics": "bad"}) == []
    with pytest.raises(OdcsValidationError):
        _raise_if_invalid(
            {"diagnostics": [{"id": "odcs:x", "severity": "error"}]},
            context="unit",
        )


def test_validate_raises_on_serde_error() -> None:
    with pytest.raises(OdcsValidationError, match="validate"):
        validate_odcs_document(
            {
                "apiVersion": "v3.1.0",
                "kind": "DataContract",
                "id": "x",
                "name": "X",
                "version": "1.0.0",
                "status": "draft",
                "description": "plain-string-not-allowed",
                "schema": [
                    {
                        "name": "row",
                        "logicalType": "object",
                        "properties": [{"name": "id", "logicalType": "string"}],
                    }
                ],
            }
        )


def test_import_ownership_variants_and_description() -> None:
    data = {
        "apiVersion": "v3.1.0",
        "kind": "DataContract",
        "id": "x",
        "name": "X",
        "version": "1.0.0",
        "status": "draft",
        "description": {"usage": "used for analytics"},
        "team": [
            {"username": "bob", "role": "owner", "dateIn": "2024-01-01"},
            "skip-me",
        ],
        "support": ["skip", {"channel": "email", "url": "https://example.com"}],
        "owner": {"team": "legacy-team", "contact": "legacy@example.com"},
        "schema": [
            {
                "name": "row",
                "logicalType": "object",
                "properties": [{"name": "id", "logicalType": "string"}],
            }
        ],
    }
    contract = import_odcs(data)
    assert contract.description == "used for analytics"
    assert contract.ownership is not None
    assert contract.ownership.team == "legacy-team"
    assert any(c.name == "bob" for c in contract.ownership.contacts)
    assert any(c.email == "legacy@example.com" for c in contract.ownership.contacts)

    assert import_odcs({**data, "description": "plain"}).description == "plain"
    assert import_odcs({**data, "description": {"purpose": "  "}}).description is None


def test_import_multi_object_schema_and_map_children() -> None:
    data = {
        "apiVersion": "v3.1.0",
        "kind": "DataContract",
        "id": "multi",
        "name": "Multi",
        "version": "1.0.0",
        "status": "draft",
        "schema": [
            {
                "name": "a",
                "logicalType": "object",
                "properties": [{"name": "id", "logicalType": "string"}],
            },
            {
                "name": "b",
                "logicalType": "object",
                "properties": [{"name": "label", "logicalType": "string"}],
            },
        ],
    }
    contract = import_odcs(data)
    assert [f.name for f in contract.contract_schema.fields] == ["a", "b"]

    mapped = import_odcs(
        {
            "id": "m",
            "name": "M",
            "version": "1.0.0",
            "schema": [
                {
                    "name": "attrs",
                    "logicalType": "map",
                    "items": {"name": "entry", "logicalType": "string"},
                }
            ],
        }
    )
    assert mapped.contract_schema.fields[0].children[0].name == "value"


def test_export_special_types_and_nested_children() -> None:
    contract = CanonicalContract.model_validate(
        {
            "contract_id": "types",
            "name": "Types",
            "version": "1.0.0",
            "ownership": Ownership(team="t", contacts=[]),
            "schema": {
                "fields": [
                    {"name": "email", "logical_type": "email"},
                    {"name": "uri", "logical_type": "uri"},
                    {"name": "blob", "logical_type": "binary"},
                    {
                        "name": "payload",
                        "logical_type": "object",
                        "children": [{"name": "ok", "logical_type": "boolean"}],
                    },
                    {
                        "name": "tags",
                        "logical_type": "array",
                        "children": [{"name": "a", "logical_type": "string"}],
                    },
                    {
                        "name": "score",
                        "logical_type": "integer",
                        "constraints": {"unique": True, "min_value": 0, "max_value": 10},
                    },
                ]
            },
        }
    )
    exported = export_odcs(contract)
    props = {item["name"]: item for item in exported["schema"][0]["properties"]}
    assert props["email"]["logicalTypeOptions"]["format"] == "email"
    assert props["uri"]["logicalTypeOptions"]["format"] == "uri"
    assert props["blob"]["logicalTypeOptions"]["format"] == "binary"
    assert props["payload"]["properties"][0]["name"] == "ok"
    assert props["tags"]["items"]["logicalType"] == "string"
    assert props["score"]["unique"] is True

    # Non-object field with children maps to properties for CCM fidelity (validate off).
    weird = CanonicalContract.model_validate(
        {
            "contract_id": "weird",
            "name": "Weird",
            "version": "1.0.0",
            "schema": {
                "fields": [
                    {
                        "name": "weird",
                        "logical_type": "string",
                        "children": [{"name": "nested", "logical_type": "string"}],
                    }
                ]
            },
        }
    )
    weird_export = export_odcs(weird, validate=False)
    assert weird_export["schema"][0]["properties"][0]["properties"][0]["name"] == "nested"


def test_coerce_bool_int_and_fallback() -> None:
    contract = import_odcs(
        {
            "id": "x",
            "name": "X",
            "version": "1.0.0",
            "schema": [
                {
                    "name": "flag",
                    "logicalType": "boolean",
                    "required": 0,
                    "unique": 1,
                }
            ],
        }
    )
    assert contract.contract_schema.fields[0].required is False
    assert contract.contract_schema.fields[0].constraints.unique is True
    contract2 = import_odcs(
        {
            "id": "x",
            "name": "X",
            "version": "1.0.0",
            "schema": [{"name": "flag", "logicalType": "boolean", "required": 2.5}],
        }
    )
    assert contract2.contract_schema.fields[0].required is True


def test_enum_type_without_values_raises() -> None:
    with pytest.raises(OdcsImportError, match="enum type requires"):
        import_odcs(
            {
                "id": "x",
                "name": "X",
                "version": "1.0.0",
                "schema": [{"name": "status", "logicalType": "enum"}],
            }
        )


def test_aliases_non_list_and_schema_not_list() -> None:
    contract = import_odcs(
        {
            "id": "x",
            "name": "X",
            "version": "1.0.0",
            "schema": [
                {
                    "name": "id",
                    "logicalType": "string",
                    "customProperties": [{"property": "aliases", "value": "not-a-list"}],
                }
            ],
        }
    )
    assert contract.contract_schema.fields[0].aliases == []
    empty = import_odcs({"id": "x", "name": "X", "version": "1.0.0", "schema": {}})
    assert empty.contract_schema.fields == []
