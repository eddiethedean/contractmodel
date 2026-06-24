"""DataFrame validation with optional dependencies."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from contractmodel.core.ccm import CanonicalContract
from contractmodel.core.result import ValidationErrorDetail, ValidationResult
from contractmodel.core.types import ValidationMode
from contractmodel.errors import OptionalDependencyError
from contractmodel.validation.engine import validate_records
from contractmodel.validation.limits import (
    check_row_limit,
    limit_exceeded_result,
    validate_limit_params,
)


def validate_csv(
    contract: CanonicalContract,
    path: str | Path,
    *,
    mode: ValidationMode = ValidationMode.STRICT,
    read_csv_kwargs: dict[str, Any] | None = None,
    max_rows: int | None = None,
) -> ValidationResult:
    """Validate a CSV file against a contract."""
    validate_limit_params(max_rows=max_rows)
    try:
        pd = _import_pandas()
        df = pd.read_csv(path, **(read_csv_kwargs or {}))
    except OptionalDependencyError:
        raise
    except OSError as exc:
        return limit_exceeded_result(f"Failed to read CSV file: {exc}")
    except UnicodeDecodeError as exc:
        return limit_exceeded_result(f"Failed to decode CSV file: {exc}")
    except Exception as exc:
        return limit_exceeded_result(f"Failed to parse CSV file: {exc}")
    return validate_pandas(contract, df, mode=mode, max_rows=max_rows)


def validate_parquet(
    contract: CanonicalContract,
    path: str | Path,
    *,
    mode: ValidationMode = ValidationMode.STRICT,
    read_parquet_kwargs: dict[str, Any] | None = None,
    max_rows: int | None = None,
) -> ValidationResult:
    """Validate a Parquet file against a contract."""
    validate_limit_params(max_rows=max_rows)
    try:
        pd = _import_pandas()
        try:
            import pyarrow  # noqa: F401
        except ImportError as exc:
            raise OptionalDependencyError("parquet") from exc
        df = pd.read_parquet(path, **(read_parquet_kwargs or {}))
    except OptionalDependencyError:
        raise
    except OSError as exc:
        return limit_exceeded_result(f"Failed to read Parquet file: {exc}")
    except Exception as exc:
        return limit_exceeded_result(f"Failed to parse Parquet file: {exc}")
    return validate_pandas(contract, df, mode=mode, max_rows=max_rows)


def validate_pandas(
    contract: CanonicalContract,
    df: Any,
    *,
    mode: ValidationMode = ValidationMode.STRICT,
    max_rows: int | None = None,
) -> ValidationResult:
    """Validate a Pandas DataFrame against a contract."""
    validate_limit_params(max_rows=max_rows)
    pd = _import_pandas()
    if not isinstance(df, pd.DataFrame):
        msg = "Expected a pandas.DataFrame"
        raise TypeError(msg)

    row_limit = check_row_limit(len(df), max_rows)
    if row_limit is not None:
        return row_limit

    errors = _schema_errors(contract, list(df.columns), mode)
    normalized = df.where(pd.notna(df), None)
    result = validate_records(
        contract,
        normalized.to_dict(orient="records"),
        mode=mode,
        skip_missing_field_errors=True,
    )
    errors.extend(result.errors)
    success = len(errors) == 0
    return ValidationResult(
        success=success,
        error_count=len(errors),
        warning_count=result.warning_count,
        errors=errors,
        warnings=result.warnings,
        metrics={**result.metrics, "rows_total": len(df)},
    )


def validate_polars(
    contract: CanonicalContract,
    df: Any,
    *,
    mode: ValidationMode = ValidationMode.STRICT,
    max_rows: int | None = None,
) -> ValidationResult:
    """Validate a Polars DataFrame against a contract."""
    validate_limit_params(max_rows=max_rows)
    pl = _import_polars()
    if not isinstance(df, pl.DataFrame):
        msg = "Expected a polars.DataFrame"
        raise TypeError(msg)

    row_limit = check_row_limit(len(df), max_rows)
    if row_limit is not None:
        return row_limit

    errors = _schema_errors(contract, df.columns, mode)
    result = validate_records(
        contract,
        df.to_dicts(),
        mode=mode,
        skip_missing_field_errors=True,
    )
    errors.extend(result.errors)
    success = len(errors) == 0
    return ValidationResult(
        success=success,
        error_count=len(errors),
        warning_count=result.warning_count,
        errors=errors,
        warnings=result.warnings,
        metrics={**result.metrics, "rows_total": len(df)},
    )


def _schema_errors(
    contract: CanonicalContract,
    columns: list[str],
    mode: ValidationMode,
) -> list[ValidationErrorDetail]:
    errors: list[ValidationErrorDetail] = []
    contract_fields = {field.name for field in contract.contract_schema.fields}
    column_set = set(columns)

    for field in contract.contract_schema.fields:
        if field.required and field.name not in column_set:
            errors.append(
                ValidationErrorDetail(
                    code="CM_SCHEMA_MISSING_FIELD",
                    message=f"Missing required column '{field.name}'",
                    field=field.name,
                )
            )

    if mode == ValidationMode.STRICT:
        for column in sorted(column_set - contract_fields):
            errors.append(
                ValidationErrorDetail(
                    code="CM_SCHEMA_EXTRA_FIELD",
                    message=f"Extra column '{column}' is not defined in the contract",
                    field=column,
                )
            )

    return errors


def _import_pandas() -> Any:
    try:
        import pandas as pd
    except ImportError as exc:
        raise OptionalDependencyError("pandas") from exc
    return pd


def _import_polars() -> Any:
    try:
        import polars as pl
    except ImportError as exc:
        raise OptionalDependencyError("polars") from exc
    return pl
