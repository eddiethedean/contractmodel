"""Extended semantic export tests."""

import pytest

from contractmodel.core.ccm import CanonicalContract
from contractmodel.semantic.owl import export_owl
from contractmodel.semantic.rdf import export_rdf
from contractmodel.semantic.shacl import export_shacl

rdflib = pytest.importorskip("rdflib")


def _semantic_contract() -> CanonicalContract:
    return CanonicalContract.model_validate(
        {
            "contract_id": "sem",
            "name": "Semantic",
            "version": "1.0.0",
            "semantics": {"namespaces": {"ex": "http://example.org/"}},
            "schema": {
                "fields": [
                    {
                        "name": "id",
                        "logical_type": "string",
                        "required": True,
                        "constraints": {
                            "min_length": 1,
                            "max_length": 10,
                            "pattern": "^[a-z]+$",
                            "enum_values": ["a", "b"],
                        },
                        "semantic": {
                            "iri": "http://example.org/id",
                            "ontology_class": "http://example.org/Person",
                            "ontology_property": "http://example.org/hasId",
                        },
                    },
                    {
                        "name": "count",
                        "logical_type": "integer",
                        "required": False,
                        "nullable": True,
                    },
                ]
            },
        }
    )


def test_rdf_with_semantics() -> None:
    turtle = export_rdf(_semantic_contract())
    assert "Semantic" in turtle
    assert "mapsTo" in turtle


def test_shacl_with_constraints() -> None:
    turtle = export_shacl(_semantic_contract())
    assert "sh:minLength" in turtle or "minLength" in turtle
    assert "xsd:integer" in turtle


def test_owl_with_semantics() -> None:
    turtle = export_owl(_semantic_contract())
    assert "owl:Class" in turtle
    assert "hasId" in turtle or "id" in turtle
