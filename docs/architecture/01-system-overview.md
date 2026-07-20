# System Overview

## Purpose

ContractModel provides a complete developer-first data contract lifecycle for Python.

ContractModel owns **what** a valid data contract means. Downstream tools (for
example ETLantic) own **where and when** that contract is applied. Execution
plugins own **how** a check runs on a backend. See [ROADMAP.md](../ROADMAP.md).

## Architecture

```text
External Contract Formats
  Shipped (0.2.x):
    CCM (native YAML/JSON) · ODCS · Pydantic
    JSON Schema / OpenAPI / Markdown export
    RDF / SHACL / OWL export (semantic extra)
  Planned after 0.4 (adapter/fidelity framework):
    JSON Schema import · Avro · Protobuf · Parquet schema · dbt
    AsyncAPI · Delta Lake / Iceberg · catalogs
  Full catalog: docs/roadmap/03-data-contract-formats.md
        |
        v
Import Adapters
        |
        v
Canonical Contract Model
        |
        +--> Pydantic Generator
        +--> Validation Engine
        +--> DataFrame Engine
        +--> Diff Engine
        +--> Export Engine
        +--> Plugin Manager
        +--> Semantic Engine
        +--> Registry Client
```

## Main Runtime Flow

1. A user loads a contract.
2. The loader detects or receives the source format.
3. The adapter converts it into the CCM.
4. The CCM is validated internally.
5. The user validates data, exports to another format, diffs versions, or publishes the contract.

## Non-Goals for v1

- Hosted SaaS service.
- Full dbt replacement.
- Full Great Expectations replacement.
- Full ontology reasoner.
- Distributed streaming validation engine.
- Absorbing SQL, Spark, scheduling, or pipeline orchestration (those stay in
  consumers and execution plugins).

## Current release (0.2.x)

- Stable Python API (`DataContract` facade).
- ODCS import/export.
- Pydantic V2 model generation.
- Record, JSON, CSV, Parquet, Pandas, and Polars validation.
- Contract diffing and breaking-change detection.
- CLI.
- Plugin interfaces (experimental).
- Semantic metadata export stubs.

## Toward 1.0

| Release | Focus |
|---------|--------|
| **0.2** | **Shipped** — semantic kernel: wire CCM, descriptors, fingerprints, public integration API |
| **0.3** | Bounded, redactable validation protocol |
| **0.4** | Adapter/fidelity framework; then new formats |
| **0.5–0.9** | Compatibility, trust, CLI/DX, conformance |
| **1.0** | Frozen public schemas and ETLantic-ready stable APIs |

Detail: [ROADMAP.md](../ROADMAP.md) and
[CONTRACTMODEL_UPGRADE_PLAN.md](../CONTRACTMODEL_UPGRADE_PLAN.md).
