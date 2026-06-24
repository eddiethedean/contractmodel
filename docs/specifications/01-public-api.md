# Public API Specification

## Package Exports

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
    LogicalType,
    ContractDiff,
    BreakingChange,
    NonBreakingChange,
    FieldChange,
    ChangeType,
    ContractModelError,
    OptionalDependencyError,
    OdcsImportError,
    examples,
    __version__,
)
```

## DataContract

`DataContract` is the user-facing wrapper around the CCM. Prefer factory classmethods over `__init__`.

```python
class DataContract:
    @classmethod
    def load(cls, path: str | Path) -> "DataContract": ...

    @classmethod
    def from_yaml(cls, path: str | Path) -> "DataContract": ...

    @classmethod
    def from_json(cls, path: str | Path) -> "DataContract": ...

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DataContract": ...

    @classmethod
    def from_odcs(cls, path: str | Path) -> "DataContract": ...

    @classmethod
    def from_odcs_dict(cls, data: dict[str, Any]) -> "DataContract": ...

    @classmethod
    def from_pydantic(cls, model: type[BaseModel], *, name: str | None = None) -> "DataContract": ...

    @classmethod
    def from_ccm(cls, ccm: CanonicalContract) -> "DataContract": ...

    @property
    def ccm(self) -> CanonicalContract: ...

    @property
    def import_warnings(self) -> list[ValidationWarningDetail]: ...

    @property
    def contract_id(self) -> str: ...

    @property
    def name(self) -> str: ...

    @property
    def version(self) -> str: ...

    @property
    def kind(self) -> ContractKind: ...

    @property
    def status(self) -> ContractStatus: ...

    @property
    def schema(self) -> ContractSchema: ...

    @property
    def fields(self) -> list[ContractField]: ...

    def to_pydantic(
        self,
        *,
        class_name: str | None = None,
        mode: ValidationMode = ValidationMode.STRICT,
    ) -> type[ContractModel]: ...

    def validate(
        self,
        path: str | Path,
        *,
        format: str = "auto",
        mode: ValidationMode = ValidationMode.STRICT,
        max_bytes: int | None = None,
        max_rows: int | None = None,
    ) -> ValidationResult: ...

    def validate_record(
        self,
        record: Mapping[str, Any],
        *,
        mode: ValidationMode = ValidationMode.STRICT,
    ) -> ValidationResult: ...

    def validate_records(
        self,
        records: Iterable[Mapping[str, Any]],
        *,
        mode: ValidationMode = ValidationMode.STRICT,
        max_rows: int | None = None,
    ) -> ValidationResult: ...

    def validate_json(
        self,
        data: str | bytes | Mapping[str, Any] | list[Mapping[str, Any]],
        *,
        mode: ValidationMode = ValidationMode.STRICT,
        max_bytes: int | None = None,
        max_rows: int | None = None,
    ) -> ValidationResult: ...

    def validate_csv(
        self,
        path: str | Path,
        *,
        mode: ValidationMode = ValidationMode.STRICT,
        read_csv_kwargs: dict[str, Any] | None = None,
        max_bytes: int | None = None,
        max_rows: int | None = None,
    ) -> ValidationResult: ...

    def validate_parquet(
        self,
        path: str | Path,
        *,
        mode: ValidationMode = ValidationMode.STRICT,
        read_parquet_kwargs: dict[str, Any] | None = None,
        max_bytes: int | None = None,
        max_rows: int | None = None,
    ) -> ValidationResult: ...

    def validate_pandas(
        self,
        df: Any,
        *,
        mode: ValidationMode = ValidationMode.STRICT,
        max_rows: int | None = None,
    ) -> ValidationResult: ...

    def validate_polars(
        self,
        df: Any,
        *,
        mode: ValidationMode = ValidationMode.STRICT,
        max_rows: int | None = None,
    ) -> ValidationResult: ...

    def diff(
        self,
        other: "DataContract",
        *,
        mode: CompatibilityMode = CompatibilityMode.BACKWARD,
    ) -> ContractDiff: ...

    def has_breaking_changes(
        self,
        other: "DataContract",
        *,
        mode: CompatibilityMode = CompatibilityMode.BACKWARD,
    ) -> bool: ...

    def is_breaking_change(self, other: "DataContract", *, mode: CompatibilityMode = ...) -> bool: ...

    def to_yaml(self, path: str | Path | None = None) -> str: ...

    def to_json(self, path: str | Path | None = None, *, indent: int = 2) -> str: ...

    def save(self, path: str | Path, *, format: Literal["auto", "ccm", "odcs"] = "auto") -> None: ...

    def to_odcs(self) -> dict[str, Any]: ...

    def to_json_schema(self) -> dict[str, Any]: ...

    def to_openapi(self) -> dict[str, Any]: ...

    def to_markdown(self) -> str: ...

    def to_rdf(self) -> str: ...

    def to_shacl(self) -> str: ...

    def to_owl(self) -> str: ...
```

### Diff semantics

`old_contract.diff(new_contract)` treats **self** as the old/source version and **other** as the new/target version. `ContractDiff.source_version` and `target_version` come from contract metadata.

### Pydantic model generation

`to_pydantic(mode=...)` uses the same cached generation path as `validate_*` for that mode. Generated top-level and nested object models subclass `ContractModel`.

## ContractModel

`ContractModel` is the base class for Pydantic models generated from contracts.

```python
class ContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid")
```

`DataContract.to_pydantic()` returns a subclass of `ContractModel`.

## ValidationResult

```python
class ValidationResult(BaseModel):
    success: bool
    error_count: int = 0
    warning_count: int = 0
    errors: list[ValidationErrorDetail] = Field(default_factory=list)
    warnings: list[ValidationWarningDetail] = Field(default_factory=list)
    metrics: dict[str, Any] = Field(default_factory=dict)

    def __bool__(self) -> bool: ...

    def raise_for_errors(self) -> None: ...
```

`metrics` may include `records_total`, `records_valid`, `records_invalid`, and `rows_total` (DataFrame validation).

## ValidationErrorDetail

```python
class ValidationErrorDetail(BaseModel):
    code: str
    message: str
    field: str | None = None
    row: int | None = None
    value: Any | None = None
    severity: Literal["error", "critical"] = "error"
```

## ContractDiff

```python
class ChangeType(str, Enum):
    TYPE_CHANGED = "type_changed"
    CONSTRAINTS_CHANGED = "constraints_changed"
    METADATA_CHANGED = "metadata_changed"
    MODIFIED = "modified"

class FieldChange(BaseModel):
    field: str
    change_type: ChangeType
    old_value: str | None = None
    new_value: str | None = None

class ContractDiff(BaseModel):
    source_version: str
    target_version: str
    added_fields: list[str] = Field(default_factory=list)
    removed_fields: list[str] = Field(default_factory=list)
    changed_fields: list[FieldChange] = Field(default_factory=list)
    breaking_changes: list[BreakingChange] = Field(default_factory=list)
    non_breaking_changes: list[NonBreakingChange] = Field(default_factory=list)

    @property
    def is_breaking(self) -> bool: ...
```

## Exceptions

```python
class ContractModelError(Exception): ...
class OptionalDependencyError(ContractModelError): ...
class OdcsImportError(ContractModelError): ...
class ContractPluginError(ContractModelError): ...
class RegistryError(ContractModelError): ...
```

## Examples helper

```python
from contractmodel.examples import example_path, load_example, list_examples, read_example_text
```
