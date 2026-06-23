"""Tests for OpenAPI export."""

from contractmodel import DataContract
from contractmodel.export.openapi import export_openapi


def test_export_openapi() -> None:
    contract = DataContract.from_odcs("examples/customer_events.odcs.yaml")
    doc = export_openapi(contract.ccm)
    assert doc["openapi"] == "3.1.0"
    assert "components" in doc
    assert "schemas" in doc["components"]
