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
    ContractDiff,
    BreakingChange,
)
```

## DataContract

`DataContract` is the user-facing wrapper around the CCM.

```python
class DataContract:
    @classmethod
    def from_yaml(cls, path: str | Path) -> "DataContract": ...

    @classmethod
    def from_json(cls, path: str | Path) -> "DataContract": ...

    @classmethod
    def from_odcs(cls, path: str | Path) -> "DataContract": ...

    @classmethod
    def from_pydantic(cls, model: type[BaseModel], *, name: str | None = None) -> "DataContract": ...

    @property
    def ccm(self) -> CanonicalContract: ...

    @property
    def name(self) -> str: ...

    @property
    def version(self) -> str: ...

    @property
    def fields(self) -> list[ContractField]: ...

    def to_pydantic(self, *, class_name: str | None = None) -> type[BaseModel]: ...

    def validate_record(self, record: Mapping[str, Any]) -> ValidationResult: ...

    def validate_records(self, records: Iterable[Mapping[str, Any]]) -> ValidationResult: ...

    def validate_json(self, data: str | bytes | Mapping[str, Any] | list[Mapping[str, Any]]) -> ValidationResult: ...

    def validate_csv(self, path: str | Path, **kwargs: Any) -> ValidationResult: ...

    def validate_parquet(self, path: str | Path, **kwargs: Any) -> ValidationResult: ...

    def validate_pandas(self, df: Any) -> ValidationResult: ...

    def validate_polars(self, df: Any) -> ValidationResult: ...

    def diff(self, other: "DataContract") -> ContractDiff: ...

    def is_breaking_change(self, other: "DataContract") -> bool: ...

    def to_odcs(self) -> dict[str, Any]: ...

    def to_json_schema(self) -> dict[str, Any]: ...

    def to_markdown(self) -> str: ...

    def to_rdf(self) -> str: ...

    def to_shacl(self) -> str: ...

    def to_owl(self) -> str: ...
```

## ContractModel

`ContractModel` is reserved for generated Pydantic model classes.

```python
class ContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid")
```

Generated classes should subclass `ContractModel`.

## ValidationResult

```python
class ValidationResult(BaseModel):
    success: bool
    error_count: int = 0
    warning_count: int = 0
    errors: list[ValidationErrorDetail] = Field(default_factory=list)
    warnings: list[ValidationWarningDetail] = Field(default_factory=list)
    metrics: dict[str, Any] = Field(default_factory=dict)
```

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
