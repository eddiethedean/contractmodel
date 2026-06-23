"""OWL export."""

from __future__ import annotations

from contractmodel.core.ccm import CanonicalContract
from contractmodel.errors import OptionalDependencyError


def export_owl(contract: CanonicalContract) -> str:
    """Export semantic class and property references as OWL/Turtle."""
    try:
        from rdflib import Graph, Literal, URIRef
        from rdflib.namespace import OWL, RDF, RDFS
    except ImportError as exc:
        raise OptionalDependencyError("semantic") from exc

    graph = Graph()
    graph.bind("owl", OWL)
    graph.bind("rdfs", RDFS)

    class_uri = URIRef(f"urn:contract:{contract.contract_id}/class")
    graph.add((class_uri, RDF.type, OWL.Class))
    graph.add((class_uri, RDFS.label, Literal(contract.name)))

    for field in contract.contract_schema.fields:
        if field.semantic is None:
            continue
        prop_uri = URIRef(f"urn:contract:{contract.contract_id}/prop/{field.name}")
        graph.add((prop_uri, RDF.type, OWL.DatatypeProperty))
        graph.add((prop_uri, RDFS.label, Literal(field.name)))
        if field.semantic.ontology_class:
            graph.add((prop_uri, RDFS.domain, URIRef(field.semantic.ontology_class)))
        if field.semantic.ontology_property:
            graph.add((prop_uri, OWL.equivalentProperty, URIRef(field.semantic.ontology_property)))

    return str(graph.serialize(format="turtle"))
