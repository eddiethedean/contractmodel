# Load ODCS contracts

ContractModel can load contracts from the Open Data Contract Standard (ODCS) YAML format and round-trip them through the Canonical Contract Model (CCM).

```python
from contractmodel import DataContract

contract = DataContract.from_odcs("examples/customer_events.odcs.yaml")
print(contract.name, contract.version)

# Export back to ODCS
odcs = contract.to_odcs()
```

Extensions, constraints, and `apiVersion`/`kind` metadata are preserved through import and export.

# Validate CSV data

```python
from contractmodel import DataContract
from contractmodel.core.types import ValidationMode

contract = DataContract.from_odcs("examples/customer_events.odcs.yaml")

# Validate a CSV file (requires pandas)
result = contract.validate_csv("data/events.csv", mode=ValidationMode.STRICT)
print(result.success, result.error_count)
```

Use `ValidationMode.PERMISSIVE` to allow extra columns, or `SCHEMA_ONLY` to check structure without constraint validation.

# Diff contracts for breaking changes

```python
from contractmodel import DataContract
from contractmodel.core.types import CompatibilityMode

old = DataContract.from_yaml("v1.yaml")
new = DataContract.from_yaml("v2.yaml")

diff = old.diff(new, mode=CompatibilityMode.BACKWARD)
for change in diff.breaking_changes:
    print("BREAKING:", change.message)
```

Renames detected via field aliases are classified as non-breaking when the alias links old and new names.
