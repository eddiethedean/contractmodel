# Validation error codes (`CM_*`)

Stable rule IDs for programmatic handling, SARIF output, and CI dashboards. Messages may change between releases; codes are [Tier 2 stable](https://github.com/eddiethedean/contractmodel/blob/main/STABILITY.md).

## Schema

| Code | When raised |
|------|-------------|
| `CM_SCHEMA_MISSING_FIELD` | Required field absent (record or dataset row) |
| `CM_SCHEMA_EXTRA_FIELD` | Field not in contract (`STRICT` mode) |

## Types and constraints

| Code | When raised |
|------|-------------|
| `CM_TYPE_INVALID` | Value does not match logical type |
| `CM_NULL_NOT_ALLOWED` | `null` where field is not nullable |
| `CM_CONSTRAINT_ENUM` | Value not in allowed enum |
| `CM_CONSTRAINT_MIN_VALUE` | Numeric value below minimum |
| `CM_CONSTRAINT_MAX_VALUE` | Numeric value above maximum |
| `CM_CONSTRAINT_MIN_LENGTH` | String shorter than minimum length |
| `CM_CONSTRAINT_MAX_LENGTH` | String longer than maximum length |
| `CM_CONSTRAINT_PATTERN` | String does not match regex pattern |

## Dataset

| Code | When raised |
|------|-------------|
| `CM_DATASET_UNIQUE` | Duplicate values in a unique column (DataFrame validation) |

## Quality rules

| Code | When raised |
|------|-------------|
| `CM_QUALITY_COMPLETENESS` | Completeness rule failed (e.g. row count below minimum) |
| `CM_QUALITY_FRESHNESS` | Freshness rule — **stub warning** in 0.2.x |

## Runtime

| Code | When raised |
|------|-------------|
| `CM_RUNTIME_ERROR` | JSON parse failure, unexpected validation error, or plugin failure |

## SARIF mapping

`contract validate --output sarif` sets `ruleId` to the `code` field. SARIF version is `2.1.0`.

## Example

```python
from contractmodel import DataContract, ValidationMode
from contractmodel.examples import load_example

contract = load_example("customer_events.odcs.yaml")
result = contract.validate_record({"customer_id": "x"}, mode=ValidationMode.STRICT)

for error in result.errors:
    print(error.code, error.field, error.message)
# CM_SCHEMA_MISSING_FIELD event_id ...
```
