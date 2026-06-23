"""Tests for semantic exports."""

from pathlib import Path

import pytest

from contractmodel import DataContract

rdflib = pytest.importorskip("rdflib")

EXAMPLE = Path(__file__).resolve().parents[2] / "examples/customer_events.ccm.yaml"


def test_rdf_export() -> None:
    contract = DataContract.from_yaml(EXAMPLE)
    rdf = contract.to_rdf()
    assert "@prefix" in rdf


def test_shacl_export() -> None:
    contract = DataContract.from_yaml(EXAMPLE)
    shacl = contract.to_shacl()
    assert "sh:" in shacl


def test_owl_export() -> None:
    contract = DataContract.from_yaml(EXAMPLE)
    owl = contract.to_owl()
    assert "owl:" in owl
