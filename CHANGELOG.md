# Changelog

## 0.1.1

- Fix validation engine bugs (generator uniqueness, duplicate errors, JSON handling)
- Implement validation modes: STRICT, PERMISSIVE, SCHEMA_ONLY, QUALITY_ONLY
- Improve ODCS round-trip (status, apiVersion, constraints, extensions)
- Fix diff engine backward compatibility and nested field diffing
- Add exporters: JSON Schema, OpenAPI, enriched Markdown
- Add semantic layer: RDF, SHACL, OWL (rdflib extra)
- Add plugin SDK and registry client
- Extend CLI: SARIF output, publish, fastapi init, shacl/rdf/owl export
- Move typer/rich to core dependencies; add email-validator

## 0.1.0

- Initial release with CCM, ODCS adapter, Pydantic generation, validation, diff, and CLI
