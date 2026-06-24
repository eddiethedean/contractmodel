"""Validation engine."""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from typing import Any

from pydantic import BaseModel, ValidationError

from contractmodel.adapters.pydantic import get_pydantic_model, mode_to_generation_options
from contractmodel.core.ccm import CanonicalContract
from contractmodel.core.result import (
    ValidationErrorDetail,
    ValidationResult,
    ValidationWarningDetail,
)
from contractmodel.core.types import ValidationMode
from contractmodel.validation.limits import check_byte_limit, check_row_limit
from contractmodel.validation.quality import validate_quality_rules


def _validation_model(
    contract: CanonicalContract,
    *,
    mode: ValidationMode,
) -> type[BaseModel]:
    schema_only, forbid_extra = mode_to_generation_options(mode)
    return get_pydantic_model(
        contract.model_dump_json(),
        None,
        schema_only,
        forbid_extra,
    )


def validate_record(
    contract: CanonicalContract,
    record: Mapping[str, Any],
    *,
    mode: ValidationMode = ValidationMode.STRICT,
    skip_missing_field_errors: bool = False,
    model: type[BaseModel] | None = None,
) -> ValidationResult:
    """Validate a single record against a contract."""
    if mode == ValidationMode.QUALITY_ONLY:
        return validate_quality_rules(contract, [record])

    errors: list[ValidationErrorDetail] = []
    warnings: list[ValidationWarningDetail] = []

    validation_model = model or _validation_model(contract, mode=mode)
    field_names = set(validation_model.model_fields.keys())
    payload = dict(record)

    if mode == ValidationMode.PERMISSIVE:
        payload = {k: v for k, v in payload.items() if k in field_names}
    elif mode == ValidationMode.STRICT:
        for key in sorted(set(record.keys()) - field_names):
            errors.append(
                ValidationErrorDetail(
                    code="CM_SCHEMA_EXTRA_FIELD",
                    message=f"Extra field '{key}' is not defined in the contract",
                    field=key,
                    value=record.get(key),
                )
            )

    try:
        validation_model.model_validate(payload)
    except ValidationError as exc:
        reported_extras = {e.field for e in errors if e.code == "CM_SCHEMA_EXTRA_FIELD"}
        for detail in _pydantic_errors_to_details(exc):
            if skip_missing_field_errors and detail.code == "CM_SCHEMA_MISSING_FIELD":
                continue
            if detail.code == "CM_SCHEMA_EXTRA_FIELD" and detail.field in reported_extras:
                continue
            errors.append(detail)

    if mode != ValidationMode.SCHEMA_ONLY and contract.quality is not None:
        quality_result = validate_quality_rules(contract, [record])
        errors.extend(quality_result.errors)
        warnings.extend(quality_result.warnings)

    success = len(errors) == 0
    return ValidationResult(
        success=success,
        error_count=len(errors),
        warning_count=len(warnings),
        errors=errors,
        warnings=warnings,
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
    skip_missing_field_errors: bool = False,
    max_rows: int | None = None,
) -> ValidationResult:
    """Validate multiple records against a contract."""
    record_list = list(records)
    row_limit_result = check_row_limit(len(record_list), max_rows)
    if row_limit_result is not None:
        return row_limit_result

    all_errors: list[ValidationErrorDetail] = []
    all_warnings: list[ValidationWarningDetail] = []
    total = len(record_list)
    invalid = 0

    validation_model: type[BaseModel] | None = None
    if mode != ValidationMode.QUALITY_ONLY:
        validation_model = _validation_model(contract, mode=mode)

    for index, record in enumerate(record_list):
        result = validate_record(
            contract,
            record,
            mode=mode,
            skip_missing_field_errors=skip_missing_field_errors,
            model=validation_model,
        )
        for error in result.errors:
            all_errors.append(error.model_copy(update={"row": index}))
        for warning in result.warnings:
            all_warnings.append(warning.model_copy(update={"row": index}))
        if not result.success:
            invalid += 1

    unique_fields = {f.name for f in contract.contract_schema.fields if f.constraints.unique}
    uniqueness_errors: list[ValidationErrorDetail] = []
    if unique_fields and total > 0:
        uniqueness_errors = _check_uniqueness(record_list, unique_fields)
        all_errors.extend(uniqueness_errors)

    if uniqueness_errors and invalid < total:
        invalid = max(invalid, 1)

    success = len(all_errors) == 0
    return ValidationResult(
        success=success,
        error_count=len(all_errors),
        warning_count=len(all_warnings),
        errors=all_errors,
        warnings=all_warnings,
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
    max_bytes: int | None = None,
    max_rows: int | None = None,
) -> ValidationResult:
    """Validate JSON data against a contract."""
    if isinstance(data, (str, bytes)):
        byte_limit_result = check_byte_limit(data, max_bytes)
        if byte_limit_result is not None:
            return byte_limit_result

    try:
        parsed = json.loads(data) if isinstance(data, (str, bytes)) else data
    except json.JSONDecodeError as exc:
        return ValidationResult(
            success=False,
            error_count=1,
            errors=[
                ValidationErrorDetail(
                    code="CM_RUNTIME_ERROR",
                    message=f"Invalid JSON: {exc.msg}",
                )
            ],
        )

    if isinstance(parsed, list):
        errors: list[ValidationErrorDetail] = []
        records: list[Mapping[str, Any]] = []
        for index, item in enumerate(parsed):
            if isinstance(item, dict):
                records.append(item)
            else:
                errors.append(
                    ValidationErrorDetail(
                        code="CM_RUNTIME_ERROR",
                        message="JSON array items must be objects",
                        row=index,
                        value=item,
                    )
                )
        result = validate_records(contract, records, mode=mode, max_rows=max_rows)
        merged_errors = errors + result.errors
        merged_success = len(merged_errors) == 0
        metrics = dict(result.metrics)
        metrics["records_total"] = len(parsed)
        return ValidationResult(
            success=merged_success,
            error_count=len(merged_errors),
            warning_count=result.warning_count,
            errors=merged_errors,
            warnings=result.warnings,
            metrics=metrics,
        )

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
        "string_too_short": "CM_CONSTRAINT_MIN_LENGTH",
        "string_too_long": "CM_CONSTRAINT_MAX_LENGTH",
    }
    if error_type in mapping:
        return mapping[error_type]
    if "type" in error_type:
        return "CM_TYPE_INVALID"
    if "none" in error_type or "null" in error_type:
        return "CM_NULL_NOT_ALLOWED"
    return "CM_TYPE_INVALID"


def _uniqueness_key(value: Any) -> str:
    try:
        hash(value)
    except TypeError:
        return json.dumps(value, sort_keys=True, default=str)
    return str(value)


def _check_uniqueness(
    records: list[Mapping[str, Any]],
    unique_fields: set[str],
) -> list[ValidationErrorDetail]:
    errors: list[ValidationErrorDetail] = []
    seen: dict[str, set[str]] = {field: set() for field in unique_fields}

    for index, record in enumerate(records):
        for field in unique_fields:
            value = record.get(field)
            if value is None:
                continue
            key = _uniqueness_key(value)
            if key in seen[field]:
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
                seen[field].add(key)

    return errors
