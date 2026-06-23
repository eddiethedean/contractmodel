"""ODCS adapter error and edge case tests."""

import pytest

from contractmodel.adapters.odcs import export_odcs, import_odcs
from contractmodel.core.ccm import CanonicalContract
from contractmodel.errors import OdcsImportError


def test_import_odcs_invalid_raises() -> None:
    with pytest.raises(OdcsImportError):
        import_odcs({"name": "missing id"})


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
                        "extensions": {"customKey": "customValue"},
                    }
                ]
            },
        }
    )
    odcs = export_odcs(contract)
    field = odcs["schema"][0]
    assert field["nullable"] is True
    assert field["default"] == "x"
    assert field["customKey"] == "customValue"


def test_export_status_and_extensions() -> None:
    contract = CanonicalContract.model_validate(
        {
            "contract_id": "meta",
            "name": "Meta",
            "version": "1.0.0",
            "status": "draft",
            "extensions": {"apiVersion": "v3.0.0", "kind": "DataContract", "extra": "ok"},
            "schema": {"fields": []},
        }
    )
    odcs = export_odcs(contract)
    assert odcs["status"] == "draft"
    assert odcs["apiVersion"] == "v3.0.0"
    assert odcs["extra"] == "ok"
