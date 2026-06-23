"""Validation engine."""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from typing import Any

from pydantic import ValidationError

from contractmodel.adapters.pydantic import generate_pydantic_model
from contractmodel.core.ccm import CanonicalContract
from contractmodel.core.result import ValidationErrorDetail, ValidationResult
from contractmodel.core.types import ValidationMode


def validate_record(
    contract: CanonicalContract,
    record: Mapping[str, Any],
    *,
    mode: ValidationMode = ValidationMode.STRICT,
) -> ValidationResult:
    """Validate a single record against a contract."""
    model = generate_pydantic_model(contract)
    errors: list[ValidationErrorDetail] = []

    if mode == ValidationMode.STRICT:
        extra = set(record.keys()) - set(model.model_fields.keys())
        for key in sorted(extra):
            errors.append(
                ValidationErrorDetail(
                    code="CM_SCHEMA_EXTRA_FIELD",
                    message=f"Extra field '{key}' is not defined in the contract",
                    field=key,
                    value=record.get(key),
                )
            )

    try:
        model.model_validate(dict(record))
    except ValidationError as exc:
        errors.extend(_pydantic_errors_to_details(exc))

    success = len(errors) == 0
    return ValidationResult(
        success=success,
        error_count=len(errors),
        errors=errors,
        metrics={
            "records_total": 1,
            "records_valid": 1 if success else 0,
            "records_invalid": 0 if success else 1,
        },
    )


def validate_records(
    contract: CanonicalContract,
    records: Iterable[Mapping[str, Any]],
    *,
    mode: ValidationMode = ValidationMode.STRICT,
) -> ValidationResult:
    """Validate multiple records against a contract."""
    all_errors: list[ValidationErrorDetail] = []
    total = 0
    invalid = 0

    for index, record in enumerate(records):
        result = validate_record(contract, record, mode=mode)
        for error in result.errors:
            all_errors.append(error.model_copy(update={"row": index}))
        total += 1
        if not result.success:
            invalid += 1

    unique_fields = {f.name for f in contract.schema.fields if f.constraints.unique}
    if unique_fields and total > 0:
        all_errors.extend(_check_uniqueness(contract, records, unique_fields))

    success = len(all_errors) == 0
    return ValidationResult(
        success=success,
        error_count=len(all_errors),
        errors=all_errors,
        metrics={
            "records_total": total,
            "records_valid": total - invalid,
            "records_invalid": invalid,
            "error_count": len(all_errors),
        },
    )


def validate_json(
    contract: CanonicalContract,
    data: str | bytes | Mapping[str, Any] | list[Mapping[str, Any]],
    *,
    mode: ValidationMode = ValidationMode.STRICT,
) -> ValidationResult:
    """Validate JSON data against a contract."""
    parsed = json.loads(data) if isinstance(data, (str, bytes)) else data

    if isinstance(parsed, list):
        records = [item for item in parsed if isinstance(item, dict)]
        return validate_records(contract, records, mode=mode)

    if isinstance(parsed, dict):
        return validate_record(contract, parsed, mode=mode)

    return ValidationResult(
        success=False,
        error_count=1,
        errors=[
            ValidationErrorDetail(
                code="CM_RUNTIME_ERROR",
                message="JSON data must be an object or array of objects",
            )
        ],
    )


def _pydantic_errors_to_details(exc: ValidationError) -> list[ValidationErrorDetail]:
    details: list[ValidationErrorDetail] = []
    for error in exc.errors():
        loc = error.get("loc", ())
        field = ".".join(str(part) for part in loc) if loc else None
        code = _error_type_to_code(error.get("type", ""))
        details.append(
            ValidationErrorDetail(
                code=code,
                message=error.get("msg", "Validation error"),
                field=field,
                value=error.get("input"),
            )
        )
    return details


def _error_type_to_code(error_type: str) -> str:
    mapping = {
        "missing": "CM_SCHEMA_MISSING_FIELD",
        "extra_forbidden": "CM_SCHEMA_EXTRA_FIELD",
        "enum": "CM_CONSTRAINT_ENUM",
        "greater_than_equal": "CM_CONSTRAINT_MIN_VALUE",
        "less_than_equal": "CM_CONSTRAINT_MAX_VALUE",
        "string_pattern_mismatch": "CM_CONSTRAINT_PATTERN",
        "string_too_short": "CM_CONSTRAINT_MIN_VALUE",
        "string_too_long": "CM_CONSTRAINT_MAX_VALUE",
    }
    if error_type in mapping:
        return mapping[error_type]
    if "type" in error_type:
        return "CM_TYPE_INVALID"
    if "none" in error_type or "null" in error_type:
        return "CM_NULL_NOT_ALLOWED"
    return "CM_TYPE_INVALID"


def _check_uniqueness(
    contract: CanonicalContract,
    records: Iterable[Mapping[str, Any]],
    unique_fields: set[str],
) -> list[ValidationErrorDetail]:
    del contract
    errors: list[ValidationErrorDetail] = []
    seen: dict[str, set[Any]] = {field: set() for field in unique_fields}

    for index, record in enumerate(records):
        for field in unique_fields:
            value = record.get(field)
            if value in seen[field]:
                errors.append(
                    ValidationErrorDetail(
                        code="CM_DATASET_UNIQUE",
                        message=f"Duplicate value for unique field '{field}'",
                        field=field,
                        row=index,
                        value=value,
                    )
                )
            else:
                seen[field].add(value)

    return errors
