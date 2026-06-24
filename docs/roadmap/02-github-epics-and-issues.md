# GitHub Epics and Issues

## Epic 1: Repository Bootstrap

- Create pyproject.toml.
- Configure ruff.
- Configure pytest.
- Configure mypy.
- Configure GitHub Actions.
- Add README.
- Add license.

## Epic 2: Canonical Contract Model

- Implement ContractKind.
- Implement LogicalType.
- Implement ContractField.
- Implement ContractSchema.
- Implement CanonicalContract.
- Implement Ownership.
- Implement QualitySpec.
- Implement ServiceLevelSpec.
- Implement LineageSpec.
- Implement SemanticSpec.
- Implement GovernanceSpec.

## Epic 3: ODCS Adapter

- Parse ODCS YAML.
- Map ODCS schema to CCM.
- Map ODCS quality to CCM.
- Export CCM to ODCS.
- Add round-trip tests.

## Epic 4: Pydantic Generator

- Generate model class.
- Generate field annotations.
- Generate Field constraints.
- Generate enums.
- Generate nested models.
- Add tests.

## Epic 5: Validation

- Implement validate_record.
- Implement validate_records.
- Implement validate_json.
- Implement error normalization.
- Implement ValidationResult.

## Epic 6: DataFrames

- Implement Pandas validation.
- Implement Polars validation.
- Implement CSV validation.
- Implement Parquet validation.
- Add optional extras.

## Epic 7: Diff Engine

- Implement field diff.
- Implement constraint diff.
- Implement breaking-change rules.
- Implement compatibility modes.

## Epic 8: CLI

- Implement Typer CLI.
- Add validate command.
- Add diff command.
- Add export command.
- Add generate command.
- Add doctor command.

## Epic 9: Exports

- Markdown exporter.
- JSON Schema exporter.
- OpenAPI exporter.
- ODCS exporter.

## Epic 10: Semantic Layer

- RDF exporter.
- SHACL exporter.
- OWL exporter.
- Semantic mapping tests.

## Epic 11: Format Adapters (P1 — 0.2.0)

See [03-data-contract-formats.md](03-data-contract-formats.md).

- JSON Schema import adapter.
- OpenAPI document import adapter.
- Avro import/export adapter.
- Protobuf import/export adapter.
- Parquet schema import/export adapter.
- dbt `schema.yml` import adapter.

## Epic 12: Lakehouse and Catalog Adapters (P2 — 0.3.0)

- Delta Lake table schema adapter.
- Apache Iceberg schema adapter.
- AWS Glue Data Catalog adapter.
- BigQuery schema adapter.
- Snowflake schema adapter.

## Epic 13: Event and Streaming Contracts (P2 — 0.3.0)

- AsyncAPI import/export adapter.
- CloudEvents payload binding adapter.
- Spark StructType JSON adapter.
- Kafka Schema Registry integration.

## Epic 14: Quality and Semantic Import (P3)

- Great Expectations suite import/export.
- SodaCL check import.
- LinkML import/export.
- JSON-LD contract documents.

## Epic 15: Enterprise Catalog Plugins (P3 — plugin SDK)

- DataHub exporter plugin.
- Collibra exporter plugin.
- Alation exporter plugin.
- Atlan exporter plugin.
