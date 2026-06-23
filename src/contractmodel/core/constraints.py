"""Constraint models for CCM fields and schemas."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class CustomConstraint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    type: str | None = None
    expression: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class FieldConstraints(BaseModel):
    model_config = ConfigDict(extra="forbid")

    min_value: int | float | Decimal | None = None
    max_value: int | float | Decimal | None = None
    min_length: int | None = None
    max_length: int | None = None
    pattern: str | None = None
    enum_values: list[Any] | None = None
    unique: bool = False
    immutable: bool = False
    allowed_values: list[Any] | None = None
    disallowed_values: list[Any] | None = None
    custom: list[CustomConstraint] = Field(default_factory=list)


class SchemaConstraint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    type: str | None = None
    expression: str | None = None
    fields: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
