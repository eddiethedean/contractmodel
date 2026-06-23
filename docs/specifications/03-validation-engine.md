# Validation Engine Specification

## Validation Layers

1. Structural validation
2. Type validation
3. Field constraint validation
4. Dataset constraint validation
5. Quality rule validation
6. Semantic validation

## Record Validation

Record validation uses a generated Pydantic model.

```python
result = contract.validate_record(record)
```

Expected behavior:
- Return ValidationResult.
- Do not raise for normal validation failures.
- Raise only for contract/runtime errors.

## Batch Validation

```python
result = contract.validate_records(records)
```

Behavior:
- Validate every record.
- Track row index.
- Aggregate errors.
- Include metrics:
  - records_total
  - records_valid
  - records_invalid
  - error_count

## DataFrame Validation

DataFrame validation must validate:
- Missing required columns.
- Extra columns depending on strict mode.
- Column type compatibility.
- Nullability.
- Field constraints where vectorizable.
- Dataset-level constraints such as uniqueness.

## Strictness Modes

```python
class ValidationMode(str, Enum):
    STRICT = "strict"
    PERMISSIVE = "permissive"
    SCHEMA_ONLY = "schema_only"
    QUALITY_ONLY = "quality_only"
```

## Error Codes

- CM_SCHEMA_MISSING_FIELD
- CM_SCHEMA_EXTRA_FIELD
- CM_TYPE_INVALID
- CM_NULL_NOT_ALLOWED
- CM_CONSTRAINT_MIN_VALUE
- CM_CONSTRAINT_MAX_VALUE
- CM_CONSTRAINT_PATTERN
- CM_CONSTRAINT_ENUM
- CM_DATASET_UNIQUE
- CM_QUALITY_FRESHNESS
- CM_QUALITY_COMPLETENESS
- CM_RUNTIME_ERROR
