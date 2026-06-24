"""Validation result models."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class ValidationErrorDetail(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    message: str
    field: str | None = None
    row: int | None = None
    value: Any | None = None
    severity: Literal["error", "critical"] = "error"


class ValidationWarningDetail(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    message: str
    field: str | None = None
    row: int | None = None
    value: Any | None = None


class ValidationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    success: bool
    error_count: int = 0
    warning_count: int = 0
    errors: list[ValidationErrorDetail] = Field(default_factory=list)
    warnings: list[ValidationWarningDetail] = Field(default_factory=list)
    metrics: dict[str, Any] = Field(default_factory=dict)

    def __bool__(self) -> bool:
        return self.success

    def raise_for_errors(self) -> None:
        """Raise ValueError if validation failed."""
        if not self.success:
            messages = [f"{e.code}: {e.message}" for e in self.errors]
            raise ValueError("; ".join(messages))
