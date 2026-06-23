# ContractModel

[![PyPI version](https://badge.fury.io/py/contractmodel.svg)](https://pypi.org/project/contractmodel/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![CI](https://github.com/eddiethedean/contractmodel/actions/workflows/ci.yml/badge.svg)](https://github.com/eddiethedean/contractmodel/actions/workflows/ci.yml)

Python-native data contracts built on a **Canonical Contract Model (CCM)** and **Pydantic V2**. Import contracts from ODCS, generate typed models, validate records and DataFrames, and detect breaking changes — all through one stable internal representation.

## Features

- **CCM-first architecture** — ODCS, Pydantic, and other formats adapt in and out of a single canonical model
- **ODCS import/export** — load and round-trip Open Data Contract Standard YAML
- **Pydantic generation** — produce validated model classes with constraints, enums, and nested objects
- **Validation** — records, JSON, CSV, Parquet, Pandas, and Polars (optional extras)
- **Contract diffing** — field-level changes with breaking-change classification
- **CLI** — `init`, `validate`, `diff`, `generate`, `export`, and `doctor`

## Installation

```bash
pip install contractmodel
```

Optional extras:

```bash
pip install "contractmodel[cli]"       # Typer CLI
pip install "contractmodel[pandas]"    # Pandas validation
pip install "contractmodel[polars]"    # Polars validation
pip install "contractmodel[parquet]"   # Parquet file validation
pip install "contractmodel[all]"       # everything
```

Requires Python 3.10+.

## Quick start

```python
from contractmodel import DataContract

contract = DataContract.from_odcs("examples/customer_events.odcs.yaml")
CustomerEvent = contract.to_pydantic()

result = contract.validate_record({
    "event_id": "550e8400-e29b-41d4-a716-446655440000",
    "customer_id": "C123",
    "event_timestamp": "2026-06-23T12:00:00",
    "event_type": "created",
})

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

## CLI

```bash
contract init
contract validate contract.yaml data.json
contract diff old.yaml new.yaml
contract generate pydantic contract.yaml --output models.py
contract export contract.yaml --to odcs
contract doctor
```

## Architecture

All external representations flow through the CCM:

```text
ODCS / YAML / JSON  →  CCM  →  Pydantic / Validation / Diff / Export
```

The CCM is format-agnostic. Adapters handle conversion; engines operate only on the canonical model. See [`docs/architecture/`](docs/architecture/) for details.

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
