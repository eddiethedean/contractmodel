# ContractModel

[![PyPI version](https://badge.fury.io/py/contractmodel.svg)](https://pypi.org/project/contractmodel/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![CI](https://github.com/eddiethedean/contractmodel/actions/workflows/ci.yml/badge.svg)](https://github.com/eddiethedean/contractmodel/actions/workflows/ci.yml)

Python-native data contracts built on a **Canonical Contract Model (CCM)** and **Pydantic V2**. Import contracts from ODCS, generate typed models, validate records and DataFrames, detect breaking changes, and export to JSON Schema, OpenAPI, Markdown, RDF, SHACL, and OWL — all through one stable internal representation.

## Features

- **CCM-first architecture** — ODCS, Pydantic, and other formats adapt in and out of a single canonical model
- **ODCS import/export** — load and round-trip Open Data Contract Standard YAML with constraints and extensions
- **Pydantic generation** — produce validated model classes with constraints, enums, nested objects, and reverse mapping
- **Validation modes** — `STRICT`, `PERMISSIVE`, `SCHEMA_ONLY`, and `QUALITY_ONLY`
- **Multi-format validation** — records, JSON, CSV, Parquet, Pandas, and Polars (optional extras)
- **Contract diffing** — field-level changes with breaking-change classification and rename detection
- **Exporters** — JSON Schema, OpenAPI, Markdown, ODCS, RDF, SHACL, OWL
- **Plugin SDK** — entry-point discovery for validators, exporters, and registries
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

```python
from contractmodel import DataContract
from contractmodel.core.types import ValidationMode

contract = DataContract.from_odcs("examples/customer_events.odcs.yaml")
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

Load a native CCM contract:

```python
contract = DataContract.from_yaml("examples/customer_events.ccm.yaml")
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
| `QUALITY_ONLY` | Run CCM quality rules (freshness, completeness) |

## Plugins

Register plugins via `pyproject.toml` entry points:

```toml
[project.entry-points."contractmodel.validators"]
my_validator = "my_package:MyValidator"
```

Run `contract doctor` to list discovered plugins and optional dependencies.

## Architecture

All external representations flow through the CCM:

```text
ODCS / YAML / JSON  →  CCM  →  Pydantic / Validation / Diff / Export
```

The CCM is format-agnostic. Adapters handle conversion; engines operate only on the canonical model. See [`docs/architecture/`](docs/architecture/) and [`docs/tutorials/`](docs/tutorials/) for details.

## Development

```bash
git clone https://github.com/eddiethedean/contractmodel.git
cd contractmodel
pip install -e ".[all]" pytest pytest-cov ruff mypy
pytest
ruff check src tests
mypy src
```

## License

MIT — see [LICENSE](LICENSE).
