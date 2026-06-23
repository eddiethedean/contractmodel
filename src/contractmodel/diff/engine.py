"""Contract diff engine."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from contractmodel.core.ccm import CanonicalContract
from contractmodel.core.types import CompatibilityMode
from contractmodel.diff.rules import (
    classify_field_change,
    is_removed_field_breaking,
)


class FieldChange(BaseModel):
    model_config = ConfigDict(extra="forbid")

    field: str
    change_type: str
    old_value: str | None = None
    new_value: str | None = None


class BreakingChange(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    message: str
    field: str | None = None


class NonBreakingChange(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    message: str
    field: str | None = None


class ContractDiff(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_version: str
    target_version: str
    added_fields: list[str] = Field(default_factory=list)
    removed_fields: list[str] = Field(default_factory=list)
    changed_fields: list[FieldChange] = Field(default_factory=list)
    breaking_changes: list[BreakingChange] = Field(default_factory=list)
    non_breaking_changes: list[NonBreakingChange] = Field(default_factory=list)

    @property
    def is_breaking(self) -> bool:
        return len(self.breaking_changes) > 0


def diff_contracts(
    source: CanonicalContract,
    target: CanonicalContract,
    *,
    mode: CompatibilityMode = CompatibilityMode.BACKWARD,
) -> ContractDiff:
    """Compute the diff between two contracts."""
    source_fields = {field.name: field for field in source.schema.fields}
    target_fields = {field.name: field for field in target.schema.fields}

    added = sorted(set(target_fields) - set(source_fields))
    removed = sorted(set(source_fields) - set(target_fields))

    changed_fields: list[FieldChange] = []
    breaking: list[BreakingChange] = []
    non_breaking: list[NonBreakingChange] = []

    for name in removed:
        field = source_fields[name]
        if is_removed_field_breaking(field):
            breaking.append(
                BreakingChange(
                    code="FIELD_REMOVED",
                    message=f"Required field '{name}' was removed",
                    field=name,
                )
            )
        else:
            non_breaking.append(
                NonBreakingChange(
                    code="FIELD_REMOVED",
                    message=f"Optional field '{name}' was removed",
                    field=name,
                )
            )

    for name in added:
        field = target_fields[name]
        if field.required and not field.nullable:
            if mode == CompatibilityMode.FORWARD:
                breaking.append(
                    BreakingChange(
                        code="FIELD_ADDED",
                        message=f"Required field '{name}' was added",
                        field=name,
                    )
                )
            else:
                non_breaking.append(
                    NonBreakingChange(
                        code="FIELD_ADDED",
                        message=f"Field '{name}' was added",
                        field=name,
                    )
                )
        else:
            non_breaking.append(
                NonBreakingChange(
                    code="FIELD_ADDED",
                    message=f"Optional field '{name}' was added",
                    field=name,
                )
            )

    for name in sorted(set(source_fields) & set(target_fields)):
        old_field = source_fields[name]
        new_field = target_fields[name]
        if old_field == new_field:
            continue

        changed_fields.append(
            FieldChange(
                field=name,
                change_type="modified",
                old_value=old_field.logical_type.value,
                new_value=new_field.logical_type.value,
            )
        )

        field_breaking, field_non_breaking = classify_field_change(old_field, new_field, mode=mode)
        for message in field_breaking:
            breaking.append(BreakingChange(code="FIELD_CHANGED", message=message, field=name))
        for message in field_non_breaking:
            non_breaking.append(
                NonBreakingChange(code="FIELD_CHANGED", message=message, field=name)
            )

    return ContractDiff(
        source_version=source.version,
        target_version=target.version,
        added_fields=added,
        removed_fields=removed,
        changed_fields=changed_fields,
        breaking_changes=breaking,
        non_breaking_changes=non_breaking,
    )
