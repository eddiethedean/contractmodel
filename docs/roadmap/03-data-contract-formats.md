# Data Contract Formats Roadmap

All external formats adapt **in** and **out** of the [Canonical Contract Model (CCM)](../architecture/02-canonical-contract-model.md). Adapters never bypass the CCM.

## Status legend

| Status | Meaning |
|--------|---------|
| **Shipped** | Import and/or export available in the current release |
| **Partial** | One direction only, lossy round-trip, or experimental |
| **Planned** | On the roadmap; not yet implemented |
| **Plugin** | Intended for third-party entry points, not core |
| **Out of scope** | Explicitly not a core adapter target |

## Priority tiers

Aligned with [ROADMAP.md](../ROADMAP.md): semantic kernel and validation come
before expanding the adapter set.

| Tier | Target release | Goal |
|------|----------------|------|
| **P0** | 0.1.x | Formats required for a credible 0.1 data-contract library |
| **P1** | 0.4.x+ | High-demand interchange after the adapter/fidelity framework |
| **P2** | Later 0.x | Lakehouse, streaming, and enterprise catalog integration |
| **P3** | Future | Ecosystem-specific or plugin-only formats |

---

## Native (CCM)

| Format | Import | Export | Status | Tier | Notes |
|--------|--------|--------|--------|------|-------|
| **CCM YAML** | Shipped | Shipped | **Shipped** | P0 | Native contract authoring format |
| **CCM JSON** | Shipped | Shipped | **Shipped** | P0 | Machine-readable CCM serialization |

---

## Open standards and schema languages

| Format | Import | Export | Status | Tier | Notes |
|--------|--------|--------|--------|------|-------|
| **ODCS** (Open Data Contract Standard) | Shipped | Shipped | **Shipped** | P0 | Primary external contract standard; extensions preserved |
| **JSON Schema** (Draft 2020-12) | Planned | Shipped | **Partial** | P1 | Export complete; import adapter needed for round-trip |
| **OpenAPI 3.x** | Planned | Shipped | **Partial** | P1 | Schema object export; full document import/export later |
| **AsyncAPI 2.x / 3.x** | Planned | Planned | **Planned** | P2 | Event-driven and messaging contracts |
| **Avro** | Planned | Planned | **Planned** | P1 | `.avsc` records; common in Kafka pipelines |
| **Protobuf** | Planned | Planned | **Planned** | P1 | `.proto` messages; gRPC and analytics stacks |
| **Parquet schema** | Planned | Planned | **Planned** | P1 | Logical type mapping from Parquet primitive types |
| **SQL DDL** | Planned | Planned | **Planned** | P2 | `CREATE TABLE` subset for warehouse contracts |
| **W3C CSV Schema** | Planned | Planned | **Planned** | P3 | Column-level CSV contracts |
| **XML Schema (XSD)** | Planned | Planned | **Planned** | P3 | Legacy enterprise interchange |

---

## Python and validation ecosystems

| Format | Import | Export | Status | Tier | Notes |
|--------|--------|--------|--------|------|-------|
| **Pydantic V2 models** | Shipped | Shipped | **Shipped** | P0 | `from_pydantic` / `to_pydantic` |
| **Python type hints** (inspect) | Planned | Planned | **Planned** | P2 | Dataclasses, TypedDict, Annotated |
| **Great Expectations** | Planned | Planned | **Planned** | P2 | Expectation suites ↔ CCM quality rules |
| **Soda Core / SodaCL** | Planned | Planned | **Planned** | P3 | Check definitions as quality rules |
| **Pandera** | Plugin | Plugin | **Plugin** | P3 | DataFrame schema validation bridge |

---

## Analytics, transformation, and orchestration

| Format | Import | Export | Status | Tier | Notes |
|--------|--------|--------|--------|------|-------|
| **dbt** (`schema.yml`, model contracts) | Planned | Planned | **Planned** | P1 | Column tests and model metadata; not a full dbt replacement |
| **dbt Mesh** (cross-project contracts) | Planned | Planned | **Planned** | P2 | Contract nodes and dependencies |
| **Spark StructType** (JSON) | Planned | Planned | **Planned** | P2 | PySpark schema interchange |
| **Apache Flink** table schema | Planned | Planned | **Planned** | P3 | Stream/batch table contracts |

---

## Lakehouse and catalog formats

| Format | Import | Export | Status | Tier | Notes |
|--------|--------|--------|--------|------|-------|
| **Delta Lake** | Planned | Planned | **Planned** | P2 | Table schema + constraints from Delta metadata |
| **Apache Iceberg** | Planned | Planned | **Planned** | P2 | Schema evolution and partition specs |
| **Apache Hive** | Planned | Planned | **Planned** | P3 | Metastore DDL and serde schema |
| **AWS Glue Data Catalog** | Planned | Planned | **Planned** | P2 | Glue table definitions |
| **Google BigQuery** | Planned | Planned | **Planned** | P2 | Table schema JSON |
| **Snowflake** | Planned | Planned | **Planned** | P2 | INFORMATION_SCHEMA / YAML exports |

---

## Semantic and knowledge-graph formats

| Format | Import | Export | Status | Tier | Notes |
|--------|--------|--------|--------|------|-------|
| **RDF / Turtle** | Planned | Shipped | **Partial** | P1 | Export via `contractmodel[semantic]` |
| **SHACL** | Planned | Shipped | **Partial** | P1 | Shapes from field constraints |
| **OWL** | Planned | Shipped | **Partial** | P1 | Lightweight ontology stubs |
| **LinkML** | Planned | Planned | **Planned** | P2 | Schema + semantic class bindings |
| **JSON-LD** | Planned | Planned | **Planned** | P2 | Linked-data contract documents |

---

## Documentation and human-readable exports

| Format | Import | Export | Status | Tier | Notes |
|--------|--------|--------|--------|------|-------|
| **Markdown** | Planned | Shipped | **Partial** | P0 | Human-readable contract docs |
| **HTML** | Planned | Planned | **Planned** | P3 | Rendered contract site export |

---

## Event and messaging contracts

| Format | Import | Export | Status | Tier | Notes |
|--------|--------|--------|--------|------|-------|
| **CloudEvents** | Planned | Planned | **Planned** | P2 | Event envelope + payload schema binding |
| **Kafka Schema Registry** (Avro/JSON/Protobuf refs) | Planned | Planned | **Planned** | P2 | Subject versioning alongside Avro/Protobuf adapters |

---

## Registry and governance platforms

| Format | Import | Export | Status | Tier | Notes |
|--------|--------|--------|--------|------|-------|
| **ContractHub API** (CCM/ODCS JSON) | Partial | Partial | **Partial** | P1 | HTTP client; publish/fetch experimental |
| **DataHub** | Plugin | Plugin | **Plugin** | P3 | Ingest via `contractmodel.exporters` |
| **Collibra** | Plugin | Plugin | **Plugin** | P3 | Enterprise catalog export |
| **Alation** | Plugin | Plugin | **Plugin** | P3 | Enterprise catalog export |
| **Atlan** | Plugin | Plugin | **Plugin** | P3 | Enterprise catalog export |

---

## Data file formats (validation targets, not contract schemas)

These are **data interchange** formats validated *against* a contract, not contract definition formats themselves.

| Format | Validation | Status | Tier | Notes |
|--------|------------|--------|------|-------|
| **JSON** | Shipped | **Shipped** | P0 | Records and arrays |
| **CSV** | Shipped | **Shipped** | P0 | Via Pandas optional extra |
| **Parquet** | Shipped | **Shipped** | P0 | Via Pandas + PyArrow extras |
| **Pandas DataFrame** | Shipped | **Shipped** | P0 | Optional extra |
| **Polars DataFrame** | Shipped | **Shipped** | P0 | Optional extra |
| **NDJSON / JSON Lines** | Planned | **Planned** | P1 | Streaming batch validation |
| **ORC** | Planned | **Planned** | P3 | Columnar validation |
| **Feather / Arrow IPC** | Planned | **Planned** | P3 | In-memory columnar |

---

## Implementation phases (format adapters)

Per [ROADMAP.md](../ROADMAP.md), **0.4** publishes the adapter/fidelity
protocol. New formats follow that protocol rather than defining semantics
incrementally.

### After 0.4 — P1 interchange

- Graduate ODCS under the adapter protocol
- JSON Schema import (export already shipped)
- OpenAPI document import (schema components → CCM)
- Avro import/export
- Protobuf import/export
- Parquet schema import/export
- dbt `schema.yml` import (columns, tests, descriptions)

### Later 0.x — P2 lakehouse and events

- Delta Lake table schema adapter
- Apache Iceberg schema adapter
- AWS Glue / BigQuery / Snowflake catalog adapters
- AsyncAPI adapter
- CloudEvents payload binding
- Spark StructType JSON adapter

### Future — P3 ecosystem and plugins

- Great Expectations / Soda bridges
- LinkML / JSON-LD semantic import
- Enterprise catalog plugins (DataHub, Collibra, Alation)
- W3C CSV Schema, XSD, Hive, ORC

---

## Adapter requirements (all formats)

Every format adapter must:

1. Convert to or from `CanonicalContract` (never skip the CCM).
2. Report lossy transformations via structured fidelity results (exact,
   normalized, extended, lossy, unsupported, or rejected).
3. Include round-trip tests where bidirectional support is claimed.
4. Document unsupported CCM fields explicitly in adapter README notes.
5. Register as a core adapter or `contractmodel.exporters` / import entry point when appropriate.
6. Declare format/version ranges, capabilities, and dependency tier via the
   0.4+ adapter protocol when available.

---

## Related documents

- [ROADMAP.md](../ROADMAP.md) — active 0.2 → 1.0 release plan
- [Upgrade plan](../CONTRACTMODEL_UPGRADE_PLAN.md) — findings and acceptance criteria
- [System overview](../architecture/01-system-overview.md) — adapter architecture
- [ODCS mapping spec](../specifications/02-odcs-pydantic-mapping.md) — reference adapter design
- [Historical bootstrap](01-implementation-roadmap.md) — completed phases 0–11
- [GitHub epics](02-github-epics-and-issues.md) — tracking epics per format group
- [STABILITY.md](https://github.com/eddiethedean/contractmodel/blob/main/STABILITY.md) — API stability tiers
