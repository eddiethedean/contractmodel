# Contract Diff and Evolution Specification

## Purpose

The diff engine determines whether a contract change is safe.

## Breaking Changes

The following are breaking:
- Removing a required field.
- Renaming a field without alias.
- Changing a type incompatibly.
- Changing nullable from true to false.
- Changing required from false to true.
- Tightening constraints.
- Removing enum values.
- Reducing max_length.
- Increasing min_length.
- Adding uniqueness constraints.
- Adding non-null constraints.

## Non-Breaking Changes

The following are non-breaking:
- Adding optional field.
- Adding nullable field.
- Loosening constraints.
- Adding descriptions.
- Adding examples.
- Adding aliases.
- Adding governance metadata.
- Adding semantic mappings.

## Compatibility Modes

```python
class CompatibilityMode(str, Enum):
    BACKWARD = "backward"
    FORWARD = "forward"
    FULL = "full"
    NONE = "none"
```

## API

```python
diff = old.diff(new)
diff.is_breaking
diff.breaking_changes
```

## CLI

```bash
contract diff old.yaml new.yaml --mode backward
```

Exit codes:
- 0: compatible
- 1: breaking change
- 2: invalid contract
