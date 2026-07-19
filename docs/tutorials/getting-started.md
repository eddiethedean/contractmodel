# Getting started

## Load ODCS contracts

ContractModel loads contracts from the **Open Data Contract Standard (ODCS)** YAML format and round-trips them through the **Canonical Contract Model (CCM)**.

```python
from contractmodel import DataContract
from contractmodel.examples import load_example, example_path

# After pip install — bundled examples
contract = load_example("customer_events.odcs.yaml")
print(contract.name, contract.version)

# From a git clone — repository paths also work
contract = DataContract.from_odcs("examples/customer_events.odcs.yaml")

# Export back to ODCS
odcs = contract.to_odcs()
```

Extensions, constraints, and `apiVersion`/`kind` metadata are preserved through import and export.

## Validate CSV data

```python
from contractmodel import DataContract, ValidationMode
from contractmodel.examples import example_path, load_example

contract = load_example("customer_events.odcs.yaml")

# Validate a CSV file (requires contractmodel[pandas])
result = contract.validate_csv(
    example_path("data/events.csv"),
    mode=ValidationMode.STRICT,
)
print(result.success, result.error_count)
```

Use `ValidationMode.PERMISSIVE` to allow extra columns, or `SCHEMA_ONLY` to check structure without constraint validation.

## Diff contracts for breaking changes

```python
from contractmodel import DataContract, CompatibilityMode

old = DataContract.from_yaml("v1.yaml")
new = DataContract.from_yaml("v2.yaml")

diff = old.diff(new, mode=CompatibilityMode.BACKWARD)
for change in diff.breaking_changes:
    print("BREAKING:", change.message)
```

Renames detected via field aliases are classified as non-breaking when the alias links old and new names.

## Next steps

- [CLI walkthrough](cli-walkthrough.md)
- [Error code catalog](../reference/error-codes.md)
- [API reference](../reference/api.md)
- [Roadmap](../ROADMAP.md) — what lands in 0.2+
