"""RDF export."""

from __future__ import annotations

from typing import Any

from contractmodel.core.ccm import CanonicalContract
from contractmodel.errors import OptionalDependencyError


def export_rdf(contract: CanonicalContract) -> str:
    """Export contract semantics as Turtle RDF."""
    Graph, Literal, Namespace, URIRef = _import_rdflib()

    graph = Graph()
    contract_uri = URIRef(f"urn:contract:{contract.contract_id}")
    graph.add(
        (
            contract_uri,
            URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"),
            URIRef("urn:contract:DataContract"),
        )
    )
    graph.add((contract_uri, URIRef("urn:contract:name"), Literal(contract.name)))
    graph.add((contract_uri, URIRef("urn:contract:version"), Literal(contract.version)))

    if contract.semantics:
        for prefix, uri in contract.semantics.namespaces.items():
            graph.bind(prefix, Namespace(uri))

    for field in contract.contract_schema.fields:
        if field.semantic is None:
            continue
        field_uri = URIRef(f"urn:contract:{contract.contract_id}/field/{field.name}")
        if field.semantic.iri:
            graph.add((field_uri, URIRef("urn:contract:mapsTo"), URIRef(field.semantic.iri)))
        if field.semantic.ontology_class:
            graph.add(
                (
                    field_uri,
                    URIRef("urn:contract:ontologyClass"),
                    Literal(field.semantic.ontology_class),
                )
            )
        if field.semantic.ontology_property:
            graph.add(
                (
                    field_uri,
                    URIRef("urn:contract:ontologyProperty"),
                    Literal(field.semantic.ontology_property),
                )
            )

    return str(graph.serialize(format="turtle"))


def _import_rdflib() -> tuple[Any, Any, Any, Any]:
    try:
        from rdflib import Graph, Literal, Namespace, URIRef
    except ImportError as exc:
        raise OptionalDependencyError("semantic") from exc
    return Graph, Literal, Namespace, URIRef
