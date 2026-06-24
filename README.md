# ContractModel

[![PyPI version](https://badge.fury.io/py/contractmodel.svg)](https://pypi.org/project/contractmodel/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![CI](https://github.com/eddiethedean/contractmodel/actions/workflows/ci.yml/badge.svg)](https://github.com/eddiethedean/contractmodel/actions/workflows/ci.yml)
[![Stability: 0.1.x](https://img.shields.io/badge/stability-0.1.x-orange.svg)](STABILITY.md)

**Python-native data contracts** — import from [ODCS](https://github.com/bitol-io/open-data-contract-standard) (Open Data Contract Standard), validate with Pydantic, diff versions, and export to JSON Schema, OpenAPI, and more.

Also known as: `pip install contractmodel` · CLI command `contract`

## Who this is for

- **Data platform engineers** who want ODCS YAML contracts to drive runtime validation in Python pipelines
- **API and analytics teams** who need typed Pydantic models generated from a shared contract, not hand-maintained duplicates
- **Governance-minded teams** who want breaking-change detection when contracts evolve

## Glossary

| Term | Meaning |
|------|---------|
| **CCM** | Canonical Contract Model — ContractModel's internal, format-agnostic contract representation |
| **ODCS** | Open Data Contract Standard — YAML contract format from [Bitol](https://bitol.io/) |
| **DataContract** | Main Python class — load, validate, diff, and export contracts |
| **`contract`** | CLI installed with the package (`contract validate`, `contract diff`, …) |

## Why ContractModel?

| Approach | What you get | Gap |
|----------|--------------|-----|
| **Pydantic alone** | Fast record validation | No ODCS import, no contract diffing, no shared governance format |
| **Great Expectations / Soda** | Data quality suites | Not contract-first; weak ODCS/CCM round-trip |
| **Raw ODCS tooling** | Standard YAML contracts | No unified validation, diff, and Pydantic generation in one library |
| **ContractModel** | CCM hub: ODCS ↔ Pydantic ↔ validation ↔ diff ↔ export | 0.1.x — see [STABILITY.md](STABILITY.md) for experimental areas |

> **0.1.x stability** — Core `DataContract` APIs are stable; plugins, registry publish, and some quality rules are experimental. See [STABILITY.md](STABILITY.md) before adopting in production.

## Features

- **CCM-first architecture** — ODCS, Pydantic, and other formats adapt in and out of a single canonical model
- **ODCS import/export** — load and round-trip Open Data Contract Standard YAML with constraints and extensions
- **Pydantic generation** — produce validated model classes with constraints, enums, nested objects, and reverse mapping
- **Validation modes** — `STRICT`, `PERMISSIVE`, `SCHEMA_ONLY`, and `QUALITY_ONLY`
- **Multi-format validation** — records, JSON, CSV, Parquet, Pandas, and Polars (optional extras)
- **Contract diffing** — field-level changes with breaking-change classification and rename detection
- **Exporters** — JSON Schema, OpenAPI, Markdown, ODCS, RDF, SHACL, OWL
- **Plugin SDK (experimental)** — entry-point hooks for validators, exporters, and registries
- **CLI** — `init`, `validate`, `diff`, `generate`, `export`, `publish`, and `doctor`

## Installation

```bash
pip install contractmodel
```

Optional extras:

```bash
pip install "contractmodel[pandas]"    # Pandas validation
pip install "contractmodel[polars]"    # Polars validation
pip install "contractmodel[parquet]"   # Parquet file validation
pip install "contractmodel[semantic]"  # RDF / SHACL / OWL export
pip install "contractmodel[all]"       # everything
```

Requires Python 3.10+. The `contract` CLI is included in the base install.

## Quick start

Works after `pip install` — examples ship inside the package:

```python
from contractmodel import DataContract, ValidationMode
from contractmodel.examples import load_example

contract = load_example("customer_events.odcs.yaml")
CustomerEvent = contract.to_pydantic()

result = contract.validate_record(
    {
        "event_id": "550e8400-e29b-41d4-a716-446655440000",
        "customer_id": "C123",
        "event_timestamp": "2026-06-23T12:00:00",
        "event_type": "created",
    },
    mode=ValidationMode.STRICT,
)

print(result.success)  # True
```

From a git clone you can also use repository paths (`examples/...`). See [examples/README.md](examples/README.md).

Load a native CCM contract:

```python
from contractmodel.examples import example_path

contract = DataContract.from_yaml(example_path("customer_events.ccm.yaml"))
```

Compare contract versions:

```python
diff = old_contract.diff(new_contract)
print(diff.is_breaking)
```

Export formats:

```python
contract.to_json_schema()
contract.to_openapi()
contract.to_markdown()
contract.to_odcs()
contract.to_shacl()  # requires contractmodel[semantic]
```

## CLI

```bash
contract init contract.yaml
contract init myapp --template fastapi
contract validate contract.yaml data.json
contract validate contract.yaml data.json --output sarif
contract diff old.yaml new.yaml
contract generate pydantic contract.yaml --output models.py
contract export contract.yaml --to json-schema
contract export contract.yaml --to shacl
contract publish contract.yaml --registry https://registry.example.com
contract doctor
```

## Validation modes

| Mode | Behavior |
|------|----------|
| `STRICT` | Reject extra fields; full constraint validation |
| `PERMISSIVE` | Allow extra fields |
| `SCHEMA_ONLY` | Structure and types only |
| `QUALITY_ONLY` | Run CCM quality rules (completeness; freshness is a stub warning) |

## Performance

Validation loads full datasets into memory. For 0.1.x, keep files under **~100 MB** and **~1 million rows** unless you benchmark larger workloads. Call `to_pydantic()` once per contract and reuse the model class.

## Plugins (experimental)

Register plugins via `pyproject.toml` entry points. Installed plugins run after built-in validation and can extend export/publish when their `target` matches the requested format.

```toml
[project.entry-points."contractmodel.validators"]
my_validator = "my_package:MyValidator"
```

Run `contract doctor` to list plugin names (without loading plugin code). See [STABILITY.md](STABILITY.md) for API guarantees.

## Security

See [SECURITY.md](SECURITY.md) for registry trust, plugin install guidance, and data file limits.

## Documentation

- [Docs index](docs/README.md) — tutorials, API reference, architecture
- [Getting started tutorial](docs/tutorials/getting-started.md)
- [Error code catalog](docs/reference/error-codes.md) — `CM_*` codes for CI and SARIF
- [Architecture](docs/architecture/) and [format roadmap](docs/roadmap/03-data-contract-formats.md)

## Architecture

All external representations flow through the CCM:

```text
ODCS / YAML / JSON  →  CCM  →  Pydantic / Validation / Diff / Export
```

The CCM is format-agnostic. Adapters handle conversion; engines operate only on the canonical model.

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md) for setup, pre-commit, and PR expectations.

```bash
git clone https://github.com/eddiethedean/contractmodel.git
cd contractmodel
pip install -e ".[all]" --group dev
pre-commit install
pytest
```

## License

MIT — see [LICENSE](LICENSE).
