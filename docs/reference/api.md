# API reference

User-facing API for ContractModel 0.1.x. See [STABILITY.md](https://github.com/eddiethedean/contractmodel/blob/main/STABILITY.md) for stability tiers.

## Package exports

```python
from contractmodel import (
    DataContract,
    ContractModel,
    CanonicalContract,
    ContractField,
    ContractSchema,
    ValidationResult,
    ValidationErrorDetail,
    ValidationWarningDetail,
    ValidationMode,
    CompatibilityMode,
    ContractDiff,
    BreakingChange,
    NonBreakingChange,
    FieldChange,
    examples,
    __version__,
)
```

## DataContract

`DataContract` is the main facade around the CCM.

### Loaders

| Method | Description |
|--------|-------------|
| `from_yaml(path)` | Load CCM or ODCS YAML (auto-detected) |
| `from_json(path)` | Load CCM or ODCS JSON |
| `from_odcs(path)` | Load ODCS YAML |
| `from_odcs_dict(data)` | Load ODCS from a dict; sets `import_warnings` for lossy fields |
| `from_pydantic(model, name=None)` | Build contract from a Pydantic model class |
| `from_ccm(ccm)` | Wrap an existing `CanonicalContract` |

### Properties

| Property | Description |
|----------|-------------|
| `ccm` | Underlying `CanonicalContract` |
| `name`, `version` | Contract metadata |
| `fields` | Schema fields |
| `import_warnings` | Warnings from lossy ODCS import |

### Validation

| Method | Description |
|--------|-------------|
| `validate_record(record, mode=STRICT)` | Single mapping |
| `validate_records(records, mode=STRICT)` | Iterable of mappings |
| `validate_json(data, mode=STRICT)` | JSON string/bytes or dict/list |
| `validate_csv(path, mode=STRICT, **kwargs)` | CSV file — requires `[pandas]` |
| `validate_parquet(path, mode=STRICT, **kwargs)` | Parquet — requires `[parquet]` |
| `validate_pandas(df, mode=STRICT)` | Pandas DataFrame — requires `[pandas]` |
| `validate_polars(df, mode=STRICT)` | Polars DataFrame — requires `[polars]` |

### Diff and export

| Method | Description |
|--------|-------------|
| `diff(other, mode=BACKWARD)` | Compare to another contract |
| `is_breaking_change(other, mode=BACKWARD)` | Boolean shortcut |
| `to_pydantic(class_name=None)` | Generate Pydantic model (cached) |
| `to_odcs()` | ODCS dict |
| `to_json_schema()` | JSON Schema dict |
| `to_openapi()` | OpenAPI 3.1 schema object |
| `to_markdown()` | Human-readable markdown |
| `to_rdf()`, `to_shacl()`, `to_owl()` | Semantic exports — require `[semantic]` |

## Examples helper

```python
from contractmodel.examples import example_path, load_example, list_examples, read_example_text

contract = load_example("customer_events.odcs.yaml")
path = example_path("data/customer_event.json")
```

Bundled examples work after `pip install`. Git clones also resolve `examples/` at the repository root.

## ValidationResult

```python
class ValidationResult:
    success: bool
    error_count: int
    warning_count: int
    errors: list[ValidationErrorDetail]
    warnings: list[ValidationWarningDetail]
    metrics: dict[str, Any]
```

## ValidationErrorDetail

```python
class ValidationErrorDetail:
    code: str          # CM_* code — see error catalog
    message: str
    field: str | None
    row: int | None    # dataset row index when applicable
    value: Any | None
    severity: Literal["error", "critical"]
```

## ContractDiff

```python
class ContractDiff:
    is_breaking: bool
    breaking_changes: list[BreakingChange]
    non_breaking_changes: list[NonBreakingChange]
```

## Advanced: contractmodel.core

`CanonicalContract`, adapters, and validation engines live under `contractmodel.core` and subpackages. Prefer `DataContract` unless you need direct CCM access. See [specifications/01-public-api.md](../specifications/01-public-api.md) for contributor-level detail.
