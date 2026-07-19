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

## Toward 1.0 (ROADMAP)

Additional suites land with the release plan in [ROADMAP.md](../../ROADMAP.md):

| Release | Testing focus |
|---------|----------------|
| **0.3** | Validation-engine conformance; budget/redaction/cancellation properties |
| **0.4** | Golden and property-based adapter round-trips; fidelity findings |
| **0.5** | Compatibility fixtures across nested/rename/nullability/enum/constraint changes |
| **0.6** | Adversarial plugin/registry conformance |
| **0.8** | Cross-OS/Python matrices, isolated wheels, Hypothesis/fuzz corpora, performance budgets |
