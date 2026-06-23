"""SHACL export."""

from __future__ import annotations

from typing import Any

from contractmodel.core.ccm import CanonicalContract, ContractField
from contractmodel.errors import OptionalDependencyError


def export_shacl(contract: CanonicalContract) -> str:
    """Export contract constraints as SHACL shapes."""
    try:
        from rdflib import Graph, URIRef
        from rdflib.namespace import SH
    except ImportError as exc:
        raise OptionalDependencyError("semantic") from exc

    graph = Graph()
    graph.bind("sh", SH)
    shape_uri = URIRef(f"urn:contract:{contract.contract_id}/shape")
    graph.add((shape_uri, SH.targetClass, URIRef(f"urn:contract:{contract.contract_id}/Record")))

    for field in contract.contract_schema.fields:
        prop_uri = URIRef(f"urn:contract:{contract.contract_id}/field/{field.name}")
        graph.add((shape_uri, SH.property, prop_uri))
        graph.add(
            (
                prop_uri,
                SH.path,
                URIRef(f"urn:contract:{contract.contract_id}/prop/{field.name}"),
            )
        )
        _add_field_constraints(graph, prop_uri, field)

    return graph.serialize(format="turtle")


def _add_field_constraints(graph: Any, prop_uri: Any, field: ContractField) -> None:
    from rdflib import Literal
    from rdflib.namespace import SH, XSD

    if field.required and not field.nullable:
        graph.add((prop_uri, SH.minCount, Literal(1)))
    if field.constraints.min_length is not None:
        graph.add((prop_uri, SH.minLength, Literal(field.constraints.min_length)))
    if field.constraints.max_length is not None:
        graph.add((prop_uri, SH.maxLength, Literal(field.constraints.max_length)))
    if field.constraints.pattern is not None:
        graph.add((prop_uri, SH.pattern, Literal(field.constraints.pattern)))
    if field.constraints.enum_values:
        for value in field.constraints.enum_values:
            graph.add((prop_uri, SH["in"], Literal(value)))
    if field.logical_type.value == "integer":
        graph.add((prop_uri, SH.datatype, XSD.integer))
