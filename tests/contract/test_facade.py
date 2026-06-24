"""Tests for contract facade."""

from pathlib import Path

import pytest

from contractmodel import DataContract
from contractmodel.errors import OptionalDependencyError

EXAMPLES = Path(__file__).resolve().parents[2] / "examples"


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
