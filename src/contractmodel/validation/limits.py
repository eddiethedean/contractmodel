"""Validation size limits."""

from __future__ import annotations

from pathlib import Path

from contractmodel.core.result import ValidationErrorDetail, ValidationResult


def limit_exceeded_result(message: str) -> ValidationResult:
    return ValidationResult(
        success=False,
        error_count=1,
        errors=[
            ValidationErrorDetail(
                code="CM_RUNTIME_ERROR",
                message=message,
            )
        ],
    )


def check_byte_limit(data: str | bytes, max_bytes: int | None) -> ValidationResult | None:
    """Return a failed result when serialized data exceeds ``max_bytes``."""
    if max_bytes is None:
        return None
    size = len(data.encode("utf-8") if isinstance(data, str) else data)
    if size > max_bytes:
        return limit_exceeded_result(
            f"Data size {size} bytes exceeds limit of {max_bytes} bytes",
        )
    return None


def check_file_byte_limit(path: str | Path, max_bytes: int | None) -> ValidationResult | None:
    """Return a failed result when a file exceeds ``max_bytes``."""
    if max_bytes is None:
        return None
    file_path = Path(path)
    size = file_path.stat().st_size
    if size > max_bytes:
        return limit_exceeded_result(
            f"File size {size} bytes exceeds limit of {max_bytes} bytes",
        )
    return None


def check_row_limit(count: int, max_rows: int | None) -> ValidationResult | None:
    """Return a failed result when record count exceeds ``max_rows``."""
    if max_rows is None:
        return None
    if count > max_rows:
        return limit_exceeded_result(
            f"Record count {count} exceeds limit of {max_rows} rows",
        )
    return None
