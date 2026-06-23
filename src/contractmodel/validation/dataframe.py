"""DataFrame validation with optional dependencies."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from contractmodel.core.ccm import CanonicalContract
from contractmodel.core.result import ValidationErrorDetail, ValidationResult
from contractmodel.core.types import ValidationMode
from contractmodel.errors import OptionalDependencyError
from contractmodel.validation.engine import validate_records


def validate_csv(
    contract: CanonicalContract,
    path: str | Path,
    *,
    mode: ValidationMode = ValidationMode.STRICT,
    **kwargs: Any,
) -> ValidationResult:
    """Validate a CSV file against a contract."""
    pd = _import_pandas()
    df = pd.read_csv(path, **kwargs)
    return validate_pandas(contract, df, mode=mode)


def validate_parquet(
    contract: CanonicalContract,
    path: str | Path,
    *,
    mode: ValidationMode = ValidationMode.STRICT,
    **kwargs: Any,
) -> ValidationResult:
    """Validate a Parquet file against a contract."""
    pd = _import_pandas()
    try:
        import pyarrow  # noqa: F401
    except ImportError as exc:
        raise OptionalDependencyError("parquet") from exc
    df = pd.read_parquet(path, **kwargs)
    return validate_pandas(contract, df, mode=mode)


def validate_pandas(
    contract: CanonicalContract,
    df: Any,
    *,
    mode: ValidationMode = ValidationMode.STRICT,
) -> ValidationResult:
    """Validate a Pandas DataFrame against a contract."""
    _import_pandas()
    errors = _schema_errors(contract, list(df.columns), mode)
    records = df.to_dict(orient="records")
    result = validate_records(contract, records, mode=mode)
    errors.extend(result.errors)
    success = len(errors) == 0
    return ValidationResult(
        success=success,
        error_count=len(errors),
        errors=errors,
        metrics={
            **result.metrics,
            "rows_total": len(df),
        },
    )


def validate_polars(
    contract: CanonicalContract,
    df: Any,
    *,
    mode: ValidationMode = ValidationMode.STRICT,
) -> ValidationResult:
    """Validate a Polars DataFrame against a contract."""
    pl = _import_polars()
    if not isinstance(df, pl.DataFrame):
        msg = "Expected a polars.DataFrame"
        raise TypeError(msg)

    errors = _schema_errors(contract, df.columns, mode)
    records = df.to_dicts()
    result = validate_records(contract, records, mode=mode)
    errors.extend(result.errors)
    success = len(errors) == 0
    return ValidationResult(
        success=success,
        error_count=len(errors),
        errors=errors,
        metrics={
            **result.metrics,
            "rows_total": len(df),
        },
    )


def _schema_errors(
    contract: CanonicalContract,
    columns: list[str],
    mode: ValidationMode,
) -> list[ValidationErrorDetail]:
    errors: list[ValidationErrorDetail] = []
    contract_fields = {field.name for field in contract.schema.fields}
    column_set = set(columns)

    for field in contract.schema.fields:
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
