# Semantic Contract Extension Specification

## Purpose

Semantic contracts connect operational data fields to ontology concepts.

## Field Mapping

```yaml
name: customer_id
logical_type: string
semantic:
  ontology_class: cdao:Person
  ontology_property: cdao:hasIdentifier
  iri: https://example.mil/ontology/personIdentifier
  same_as:
    - schema:identifier
```

## Namespace Registry

```yaml
semantics:
  namespaces:
    cdao: https://example.mil/cdao#
    schema: https://schema.org/
```

## Exports

### RDF

Contract fields become RDF properties.

### SHACL

Contract constraints become SHACL shapes.

### OWL

Contract semantic classes and properties become OWL references.

## v1 Scope

- Preserve semantic mappings.
- Export basic RDF.
- Export basic SHACL.
- Export basic OWL references.
- No full ontology reasoning in core.

## v2 Scope

- Optional ontology validation.
- Namespace resolution.
- Knowledge graph synchronization.
