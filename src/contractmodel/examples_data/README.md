# ContractModel examples

Sample contracts and data for tutorials, tests, and quick starts.

> When adding or changing files here, mirror them to `src/contractmodel/examples_data/` (shipped in the PyPI wheel).

## Contract files

| File | Format | Description |
|------|--------|-------------|
| `customer_events.odcs.yaml` | [ODCS](https://github.com/bitol-io/open-data-contract-standard) v3 | Customer event stream — used in README quick start |
| `customer_events.ccm.yaml` | CCM (native) | Same contract in Canonical Contract Model YAML |
| `nested_schema.ccm.yaml` | CCM | Nested objects, quality rules, and semantics |

## Sample data

| File | Description |
|------|-------------|
| `data/customer_event.json` | Valid JSON record for `customer_events` |
| `data/events.csv` | Same record as CSV for `contract validate --format csv` |

## After `pip install contractmodel`

Examples ship inside the package. Use the helper instead of hard-coded paths:

```python
from contractmodel import DataContract
from contractmodel.examples import example_path, load_example

# Load directly
contract = load_example("customer_events.odcs.yaml")

# Or pass a resolved path to from_odcs / from_yaml
contract = DataContract.from_odcs(example_path("customer_events.odcs.yaml"))
```

CLI with bundled paths:

```bash
contract validate examples/customer_events.odcs.yaml data/customer_event.json
# After pip install, use cached paths from Python:
python -c "from contractmodel.examples import example_path; print(example_path('customer_events.odcs.yaml'))"
```

## From a git clone

Paths like `examples/customer_events.odcs.yaml` work relative to the repository root:

```python
contract = DataContract.from_odcs("examples/customer_events.odcs.yaml")
```

```bash
contract validate examples/customer_events.odcs.yaml examples/data/customer_event.json
contract validate examples/customer_events.odcs.yaml examples/data/events.csv --format csv
```
