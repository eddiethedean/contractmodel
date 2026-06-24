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

## Phase 12–14: Data Contract Format Adapters

See [03-data-contract-formats.md](03-data-contract-formats.md) for the full format catalog, status, and priority tiers.

### Phase 12 — P1 interchange (target 0.2.0)

- JSON Schema import.
- OpenAPI document import.
- Avro import/export.
- Protobuf import/export.
- Parquet schema import/export.
- dbt `schema.yml` import.

### Phase 13 — P2 lakehouse and events (target 0.3.0)

- Delta Lake, Iceberg, Glue, BigQuery, Snowflake adapters.
- AsyncAPI, CloudEvents, Spark StructType adapters.

### Phase 14 — P3 ecosystem (target 0.4.0+)

- Great Expectations, Soda, LinkML, JSON-LD.
- Enterprise catalog plugins (DataHub, Collibra, Alation, Atlan).
- W3C CSV Schema, XSD, Hive, ORC.
