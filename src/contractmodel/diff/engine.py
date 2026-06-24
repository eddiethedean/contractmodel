"""Contract diff engine."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from contractmodel.core.ccm import CanonicalContract, ContractField
from contractmodel.core.types import CompatibilityMode
from contractmodel.diff.rules import (
    classify_field_change,
    detect_renames,
    is_added_field_breaking,
    is_removed_field_breaking,
)


class ChangeType(str, Enum):
    TYPE_CHANGED = "type_changed"
    CONSTRAINTS_CHANGED = "constraints_changed"
    METADATA_CHANGED = "metadata_changed"
    MODIFIED = "modified"


class FieldChange(BaseModel):
    model_config = ConfigDict(extra="forbid")

    field: str
    change_type: ChangeType
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
    source_fields = {field.name: field for field in source.contract_schema.fields}
    target_fields = {field.name: field for field in target.contract_schema.fields}

    added_names = set(target_fields) - set(source_fields)
    removed_names = set(source_fields) - set(target_fields)

    removed_map = {name: source_fields[name] for name in removed_names}
    added_map = {name: target_fields[name] for name in added_names}
    paired_removed, paired_added, rename_messages = detect_renames(removed_map, added_map)

    added = sorted(added_names - paired_added)
    removed = sorted(removed_names - paired_removed)

    changed_fields: list[FieldChange] = []
    breaking: list[BreakingChange] = []
    non_breaking: list[NonBreakingChange] = []

    for message in rename_messages:
        if "renamed" in message:
            non_breaking.append(NonBreakingChange(code="FIELD_RENAMED", message=message))
        else:
            breaking.append(BreakingChange(code="FIELD_RENAMED", message=message))

    for name in removed:
        field = source_fields[name]
        if is_removed_field_breaking(field, mode=mode):
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
        if is_added_field_breaking(field, mode=mode):
            breaking.append(
                BreakingChange(
                    code="FIELD_ADDED",
                    message=f"Required field '{name}' was added",
                    field=name,
                )
            )
        elif field.required and field.nullable:
            non_breaking.append(
                NonBreakingChange(
                    code="FIELD_ADDED",
                    message=f"Required nullable field '{name}' was added",
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
        _diff_field_pair(
            name,
            old_field,
            new_field,
            mode=mode,
            changed_fields=changed_fields,
            breaking=breaking,
            non_breaking=non_breaking,
        )

    if source.governance != target.governance and target.governance is not None:
        non_breaking.append(
            NonBreakingChange(code="GOVERNANCE_CHANGED", message="Governance metadata updated")
        )
    if source.semantics != target.semantics and target.semantics is not None:
        non_breaking.append(
            NonBreakingChange(code="SEMANTICS_CHANGED", message="Semantic metadata updated")
        )

    return ContractDiff(
        source_version=source.version,
        target_version=target.version,
        added_fields=added,
        removed_fields=removed,
        breaking_changes=breaking,
        non_breaking_changes=non_breaking,
        changed_fields=changed_fields,
    )


def _diff_field_pair(
    name: str,
    old_field: ContractField,
    new_field: ContractField,
    *,
    mode: CompatibilityMode,
    changed_fields: list[FieldChange],
    breaking: list[BreakingChange],
    non_breaking: list[NonBreakingChange],
) -> None:
    if old_field == new_field:
        return

    summary = _summarize_change(old_field, new_field)
    changed_fields.append(
        FieldChange(
            field=name,
            change_type=summary,
            old_value=old_field.logical_type.value,
            new_value=new_field.logical_type.value,
        )
    )

    field_breaking, field_non_breaking = classify_field_change(old_field, new_field, mode=mode)
    for message in field_breaking:
        breaking.append(BreakingChange(code="FIELD_CHANGED", message=message, field=name))
    for message in field_non_breaking:
        non_breaking.append(NonBreakingChange(code="FIELD_CHANGED", message=message, field=name))

    if old_field.children or new_field.children:
        old_children = {child.name: child for child in old_field.children}
        new_children = {child.name: child for child in new_field.children}
        for child_name in sorted(set(old_children) | set(new_children)):
            if child_name not in old_children:
                child_field = new_children[child_name]
                if is_added_field_breaking(child_field, mode=mode):
                    breaking.append(
                        BreakingChange(
                            code="FIELD_CHANGED",
                            message=f"Nested field '{name}.{child_name}' was added",
                            field=f"{name}.{child_name}",
                        )
                    )
                else:
                    non_breaking.append(
                        NonBreakingChange(
                            code="FIELD_CHANGED",
                            message=f"Nested field '{name}.{child_name}' was added",
                            field=f"{name}.{child_name}",
                        )
                    )
            elif child_name not in new_children:
                child_field = old_children[child_name]
                if is_removed_field_breaking(child_field, mode=mode):
                    breaking.append(
                        BreakingChange(
                            code="FIELD_CHANGED",
                            message=f"Nested field '{name}.{child_name}' was removed",
                            field=f"{name}.{child_name}",
                        )
                    )
                else:
                    non_breaking.append(
                        NonBreakingChange(
                            code="FIELD_CHANGED",
                            message=f"Nested field '{name}.{child_name}' was removed",
                            field=f"{name}.{child_name}",
                        )
                    )
            else:
                _diff_field_pair(
                    f"{name}.{child_name}",
                    old_children[child_name],
                    new_children[child_name],
                    mode=mode,
                    changed_fields=changed_fields,
                    breaking=breaking,
                    non_breaking=non_breaking,
                )


def _summarize_change(old_field: ContractField, new_field: ContractField) -> ChangeType:
    if old_field.logical_type != new_field.logical_type:
        return ChangeType.TYPE_CHANGED
    if old_field.constraints != new_field.constraints:
        return ChangeType.CONSTRAINTS_CHANGED
    if old_field.description != new_field.description:
        return ChangeType.METADATA_CHANGED
    return ChangeType.MODIFIED
