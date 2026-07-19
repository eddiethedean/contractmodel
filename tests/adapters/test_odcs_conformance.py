"""Tests for pyodcs-backed ODCS conformance and native diff."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from contractmodel import DataContract, OdcsValidationError
from contractmodel.adapters.odcs_conformance import (
    diff_odcs_documents,
    validate_odcs_document,
)

EXAMPLES_DIR = Path(__file__).resolve().parents[2] / "examples"


def test_example_odcs_passes_conformance() -> None:
    data = yaml.safe_load((EXAMPLES_DIR / "customer_events.odcs.yaml").read_text())
    validate_odcs_document(data)


def test_missing_api_version_rejected() -> None:
    with pytest.raises(OdcsValidationError):
        validate_odcs_document(
            {
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


def test_export_roundtrip_stays_conformant() -> None:
    contract = DataContract.from_odcs(EXAMPLES_DIR / "customer_events.odcs.yaml")
    exported = contract.to_odcs()
    validate_odcs_document(exported)


def test_diff_odcs_detects_breaking_field_removal() -> None:
    old = DataContract.from_odcs(EXAMPLES_DIR / "customer_events.odcs.yaml")
    new_data = old.to_odcs()
    new_data["version"] = "2.0.0"
    new_data["schema"][0]["properties"] = [
        prop
        for prop in new_data["schema"][0]["properties"]
        if prop["name"] == "event_id"
    ]
    new = DataContract.from_odcs_dict(new_data)
    report = old.diff_odcs(new)
    assert report["hasBreaking"] is True
    assert diff_odcs_documents(old.to_odcs(), new.to_odcs())["hasBreaking"] is True
