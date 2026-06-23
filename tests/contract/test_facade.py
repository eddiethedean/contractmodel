"""Tests for contract facade."""

import json
from pathlib import Path

import pytest

from contractmodel import DataContract, FieldChange, NonBreakingChange
from contractmodel.errors import OptionalDependencyError

EXAMPLES = Path(__file__).resolve().parents[2] / "examples"


def test_from_json_ccm() -> None:
    path = EXAMPLES / "customer_events.ccm.yaml"
    import yaml

    json_path = path.with_suffix(".json")
    json_path.write_text(json.dumps(yaml.safe_load(path.read_text())))
    try:
        contract = DataContract.from_json(json_path)
        assert contract.name == "Customer Events"
    finally:
        json_path.unlink(missing_ok=True)


def test_to_openapi_and_markdown() -> None:
    contract = DataContract.from_odcs(EXAMPLES / "customer_events.odcs.yaml")
    assert "openapi" in contract.to_openapi()
    assert "# Customer Events" in contract.to_markdown()


def test_semantic_exports_require_extra(monkeypatch: pytest.MonkeyPatch) -> None:
    contract = DataContract.from_odcs(EXAMPLES / "customer_events.odcs.yaml")

    def _raise() -> tuple[object, object, object, object]:
        raise OptionalDependencyError("semantic")

    monkeypatch.setattr("contractmodel.semantic.rdf._import_rdflib", _raise)
    with pytest.raises(OptionalDependencyError):
        contract.to_rdf()


def test_public_exports() -> None:
    assert FieldChange is not None
    assert NonBreakingChange is not None
