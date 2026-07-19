"""ODCS adapter error and edge case tests."""

import pytest

from contractmodel.adapters.odcs import export_odcs, import_odcs
from contractmodel.adapters.odcs_conformance import validate_odcs_document
from contractmodel.core.ccm import CanonicalContract
from contractmodel.errors import OdcsImportError, OdcsValidationError


def test_import_odcs_invalid_status_raises() -> None:
    with pytest.raises(OdcsImportError, match="status"):
        import_odcs(
            {
                "apiVersion": "v3.1.0",
                "kind": "DataContract",
                "id": "x",
                "name": "X",
                "version": "1.0.0",
                "status": "not-a-status",
                "schema": [
                    {
                        "name": "row",
                        "logicalType": "object",
                        "properties": [{"name": "id", "logicalType": "string"}],
                    }
                ],
            }
        )


def test_validate_rejects_v3_0() -> None:
    with pytest.raises(OdcsValidationError):
        validate_odcs_document(
            {
                "apiVersion": "v3.0.0",
                "kind": "DataContract",
                "id": "x",
                "name": "X",
                "version": "1.0.0",
                "status": "draft",
                "schema": [
                    {
                        "name": "row",
                        "logicalType": "object",
                        "properties": [{"name": "id", "logicalType": "string"}],
                    }
                ],
            }
        )


def test_export_field_optional_attributes() -> None:
    contract = CanonicalContract.model_validate(
        {
            "contract_id": "opt",
            "name": "Opt",
            "version": "1.0.0",
            "schema": {
                "fields": [
                    {
                        "name": "id",
                        "logical_type": "string",
                        "required": False,
                        "nullable": True,
                        "default": "x",
                        "examples": ["a"],
                        "aliases": ["identifier"],
                        "extensions": {"businessName": "Identifier"},
                    }
                ]
            },
        }
    )
    odcs = export_odcs(contract)
    field = odcs["schema"][0]["properties"][0]
    assert field["businessName"] == "Identifier"
    customs = {item["property"]: item["value"] for item in field["customProperties"]}
    assert customs["nullable"] is True
    assert customs["default"] == "x"
    assert customs["aliases"] == ["identifier"]


def test_export_status_and_extensions() -> None:
    contract = CanonicalContract.model_validate(
        {
            "contract_id": "meta",
            "name": "Meta",
            "version": "1.0.0",
            "status": "draft",
            "extensions": {"apiVersion": "v3.1.0", "kind": "DataContract", "domain": "ops"},
            "schema": {"fields": [{"name": "id", "logical_type": "string"}]},
        }
    )
    odcs = export_odcs(contract)
    assert odcs["status"] == "draft"
    assert odcs["apiVersion"] == "v3.1.0"
    assert odcs["domain"] == "ops"
