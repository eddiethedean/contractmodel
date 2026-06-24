# System Overview

## Purpose

ContractModel provides a complete developer-first data contract lifecycle for Python.

## Architecture

```text
External Contract Formats
  - CCM (native YAML/JSON)
  - ODCS
  - JSON Schema
  - OpenAPI
  - Pydantic
  - Avro
  - Protobuf
  - Parquet schema
  - dbt
  - AsyncAPI
  - Delta Lake / Iceberg
  - RDF / SHACL / OWL
  - (see docs/roadmap/03-data-contract-formats.md)
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

## v1 Goals

- Stable Python API.
- ODCS import/export.
- Pydantic V2 model generation.
- Record, JSON, CSV, Parquet, Pandas, and Polars validation.
- Contract diffing and breaking-change detection.
- CLI.
- Plugin interfaces.
- Semantic metadata export stubs.
