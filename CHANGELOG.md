# Changelog

## Unreleased

### API improvements

- Generated Pydantic models now consistently subclass `ContractModel`; unified model cache shared by `to_pydantic()` and `validate_*`
- Add `DataContract.load`, `from_dict`, `validate(path)`, `to_yaml`, `to_json`, `save`, and metadata properties (`contract_id`, `kind`, `status`, `schema`)
- Add `has_breaking_changes` (keep `is_breaking_change` as alias), `ValidationResult.__bool__`, and `raise_for_errors()`
- Export `LogicalType`, `ChangeType`, and exception types from top-level package
- `FieldChange.change_type` is now a `ChangeType` enum; `validate_csv`/`validate_parquet` use typed `read_*_kwargs`
- Add method docstrings on `DataContract`; sync public API specification and reference docs

### Documentation and packaging

- Package bundled examples with `contractmodel.examples` helpers (`load_example`, `example_path`)
- Fix `nested_schema.ccm.yaml` quality rule metadata
- Add sample data (`examples/data/`) for CLI validation demos
- Rewrite README for newcomers (glossary, positioning, pip-install quick start)
- Add docs index, tutorials, API reference, and CM_* error catalog
- Add MkDocs site, CONTRIBUTING.md, CODE_OF_CONDUCT.md, and GitHub issue/PR templates
- Add PyPI metadata (urls, license, classifiers, keywords)
- Move `MANIFEST.json` to `docs/internal/`

## 0.1.2

- Add STABILITY.md and SECURITY.md; export ValidationMode, CompatibilityMode, ValidationWarningDetail from top-level package
- Cache generated Pydantic validation models per contract and mode
- Wire validator, exporter, and registry plugins into validate/export/publish paths
- Align registry client with ContractHub publish endpoint and optional bearer auth
- Harden ODCS auto-detection (`format: odcs`, stricter apiVersion heuristic)
- Document experimental plugin/quality/registry APIs and performance limits in README

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
