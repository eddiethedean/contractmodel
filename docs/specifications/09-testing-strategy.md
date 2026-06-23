# Testing Strategy

## Minimum Coverage

Target: 95%

## Test Categories

### Unit Tests

- CCM models.
- Type mapping.
- Constraint mapping.
- Validation result construction.

### Adapter Tests

- ODCS import.
- ODCS export.
- Round-trip preservation.

### Generator Tests

- Pydantic model generation.
- Nested objects.
- Arrays.
- Enums.
- Constraints.

### Validation Tests

- Valid record.
- Missing field.
- Extra field.
- Invalid type.
- Null not allowed.
- Constraint failures.
- Batch validation.

### DataFrame Tests

- Pandas schema validation.
- Polars schema validation.
- Null checks.
- Uniqueness checks.

### Diff Tests

- Added optional field.
- Removed required field.
- Type change.
- Constraint tightening.
- Constraint loosening.

### CLI Tests

- validate success.
- validate failure.
- diff breaking.
- export markdown.
- generate pydantic.

## Fixtures

Use examples in `/examples`.

## Test Philosophy

Every bug fix must include a regression test.
