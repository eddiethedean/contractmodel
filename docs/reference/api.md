# API reference

User-facing API for ContractModel **0.2.x**. See
[STABILITY.md](https://github.com/eddiethedean/contractmodel/blob/main/STABILITY.md)
for stability tiers and
[ROADMAP.md](https://github.com/eddiethedean/contractmodel/blob/main/ROADMAP.md)
for upcoming releases.

## Package exports

```python
from contractmodel import (
    DataContract,
    ContractModel,
    CanonicalContract,
    ContractField,
    ContractSchema,
    ContractDescriptor,
    LoadingPolicy,
    describe_contract,
    fingerprint_contract,
    is_contract_model,
    resolve_contract_model,
    export_ccm_json_schema,
    export_stability,
    ValidationResult,
    ValidationErrorDetail,
    ValidationWarningDetail,
    ValidationMode,
    CompatibilityMode,
    LogicalType,
    ContractDiff,
    BreakingChange,
    NonBreakingChange,
    FieldChange,
    ChangeType,
    ContractModelError,
    ContractPluginError,
    OptionalDependencyError,
    OdcsImportError,
    RegistryError,
    examples,
    __version__,
)
```

## Integration helpers (0.2)

```python
descriptor = contract.describe()  # or describe_contract(contract)
descriptor.identity.contract_id
descriptor.schema_view  # nested fields, nullability, constraints
descriptor.fingerprint
descriptor.fidelity

DataContract.load(path, policy=LoadingPolicy(max_bytes=1_000_000))
is_contract_model(MyModel)
fingerprint_contract(contract.ccm)
```

## DataContract

`DataContract` is the main facade around the CCM. Prefer factory classmethods over `__init__`.

### Loaders

| Method | Description |
|--------|-------------|
| `load(path)` | Load CCM or ODCS from `.yaml`/`.yml`/`.json` by extension |
| `from_yaml(path)` | Load CCM or ODCS YAML (auto-detected) |
| `from_json(path)` | Load CCM or ODCS JSON (auto-detected) |
| `from_dict(data)` | Load CCM or ODCS from a mapping (auto-detected) |
| `from_odcs(path)` | Load ODCS YAML or JSON |
| `from_odcs_dict(data)` | Load ODCS from a dict; sets `import_warnings` for lossy fields |
| `from_pydantic(model, name=None)` | Build contract from a Pydantic model class |
| `from_ccm(ccm)` | Wrap an existing `CanonicalContract` |

### Properties

| Property | Description |
|----------|-------------|
| `ccm` | Underlying `CanonicalContract` |
| `contract_id`, `name`, `version`, `kind`, `status` | Contract metadata |
| `schema` | Full `ContractSchema` |
| `fields` | Top-level schema fields |
| `import_warnings` | Warnings from lossy ODCS import |

### Validation

| Method | Description |
|--------|-------------|
| `validate(path, format=auto, mode=STRICT, max_bytes=None, max_rows=None)` | Validate a data file (extension-based auto format) |
| `validate_record(record, mode=STRICT)` | Single mapping |
| `validate_records(records, mode=STRICT, max_rows=None)` | Iterable of mappings |
| `validate_json(data, mode=STRICT, max_bytes=None, max_rows=None)` | JSON string/bytes or dict/list |
| `validate_csv(path, mode=STRICT, read_csv_kwargs=None, max_bytes=None, max_rows=None)` | CSV — requires `[pandas]` |
| `validate_parquet(path, mode=STRICT, read_parquet_kwargs=None, max_bytes=None, max_rows=None)` | Parquet — requires `[parquet]` |
| `validate_pandas(df, mode=STRICT, max_rows=None)` | Pandas DataFrame — requires `[pandas]` |
| `validate_polars(df, mode=STRICT, max_rows=None)` | Polars DataFrame — requires `[polars]` |

Optional `max_bytes` and `max_rows` guard validation entry points against oversized payloads. Non-positive limits raise `ValueError`. File and parse failures return a failed `ValidationResult` with `CM_RUNTIME_ERROR` instead of raising.

### Diff and export

| Method | Description |
|--------|-------------|
| `diff(other, mode=BACKWARD)` | Compare self (old) to other (new) |
| `has_breaking_changes(other, mode=BACKWARD)` | Boolean shortcut |
| `is_breaking_change(other)` | Deprecated alias for `has_breaking_changes` |
| `to_pydantic(class_name=None, mode=STRICT)` | Generate `ContractModel` subclass (shared cache with validation) |
| `to_yaml(path=None)` / `to_json(path=None)` | Serialize CCM |
| `save(path, format=auto)` | Write CCM or ODCS to disk |
| `to_odcs()` | ODCS dict |
| `to_json_schema()` | JSON Schema dict |
| `to_openapi()` | Minimal OpenAPI 3.1 document |
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
    metrics: dict[str, Any]  # e.g. records_total, rows_total

    def __bool__(self) -> bool: ...
    def raise_for_errors(self) -> None: ...
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
    changed_fields: list[FieldChange]  # change_type is ChangeType enum
```

## Advanced: contractmodel.core

`CanonicalContract`, adapters, and validation engines live under `contractmodel.core` and subpackages. Prefer `DataContract` unless you need direct CCM access. See [specifications/01-public-api.md](../specifications/01-public-api.md) for contributor-level detail.
