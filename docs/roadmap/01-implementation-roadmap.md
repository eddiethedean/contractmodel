# Implementation Roadmap

## Phase 0: Repository Bootstrap

- pyproject.toml
- src layout
- pytest
- ruff
- mypy
- pre-commit
- GitHub Actions

## Phase 1: CCM

- Implement all CCM Pydantic models.
- Add serialization tests.
- Add validation tests.

## Phase 2: ODCS Adapter

- Load ODCS YAML.
- Convert to CCM.
- Export CCM to ODCS.
- Preserve unknown fields.

## Phase 3: Pydantic Generator

- Generate Pydantic V2 models.
- Support constraints.
- Support nested objects.
- Support arrays.
- Support enums.

## Phase 4: Validation Engine

- Record validation.
- JSON validation.
- Batch validation.
- ValidationResult model.

## Phase 5: DataFrame Engine

- Pandas validation.
- Polars validation.
- CSV validation.
- Parquet validation.

## Phase 6: Diff Engine

- Field-level diff.
- Constraint diff.
- Breaking-change classification.

## Phase 7: CLI

- init
- validate
- diff
- export
- generate
- doctor

## Phase 8: Exporters

- Markdown
- JSON Schema
- OpenAPI
- ODCS

## Phase 9: Plugin SDK

- Entry point discovery.
- Validator plugins.
- Exporter plugins.
- Registry plugins.

## Phase 10: Semantic Layer

- Semantic model.
- RDF export.
- SHACL export.
- OWL export.

## Phase 11: Docs and Examples

- README.
- Tutorials.
- API reference.
- Example contracts.
