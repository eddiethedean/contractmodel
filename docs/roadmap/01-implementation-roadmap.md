# Implementation Roadmap (historical)

Phases **0–11** below are the completed 0.1.x bootstrap work.

The active 0.2 → 1.0 plan is **[ROADMAP.md](../ROADMAP.md)** (repository root;
symlinked here for the docs site). Design detail is in
[`CONTRACTMODEL_UPGRADE_PLAN.md`](../CONTRACTMODEL_UPGRADE_PLAN.md).
Format status remains in [03-data-contract-formats.md](03-data-contract-formats.md).

---

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

## Format adapters (deferred)

Earlier drafts scheduled P1 interchange adapters for 0.2.0. The active roadmap
defers new format adapters until **0.4** (adapter and fidelity framework). See
[ROADMAP.md](../ROADMAP.md) and
[03-data-contract-formats.md](03-data-contract-formats.md).
