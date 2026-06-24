# Diff workflow

Compare contract versions before deploying schema changes.

## Library API

```python
from contractmodel import DataContract, CompatibilityMode
from contractmodel.examples import load_example

v1 = load_example("customer_events.odcs.yaml")
v2 = load_example("customer_events.ccm.yaml")  # same logical contract, different format

diff = v1.diff(v2, mode=CompatibilityMode.BACKWARD)
print("breaking:", diff.is_breaking)
print("changes:", len(diff.breaking_changes) + len(diff.non_breaking_changes))
```

## Breaking vs non-breaking

`CompatibilityMode.BACKWARD` flags changes that would break existing consumers (removed fields, tightened constraints). Renames linked by field aliases may be classified as non-breaking.

```python
for change in diff.breaking_changes:
    print(change.change_type, change.field, change.message)
```

## CLI in CI

```bash
contract diff contracts/v1.yaml contracts/v2.yaml
```

Exit code is **1** when breaking changes are detected (0 otherwise) — suitable for pull-request checks without extra flags.
