"""Breaking-change classification rules."""

from __future__ import annotations

from contractmodel.core.ccm import ContractField
from contractmodel.core.constraints import FieldConstraints
from contractmodel.core.types import CompatibilityMode, LogicalType


def is_type_incompatible(old_type: LogicalType, new_type: LogicalType) -> bool:
    """Return True when a type change is incompatible."""
    if old_type == new_type:
        return False
    compatible_pairs = {
        (LogicalType.INTEGER, LogicalType.NUMBER),
        (LogicalType.INTEGER, LogicalType.DECIMAL),
        (LogicalType.NUMBER, LogicalType.DECIMAL),
        (LogicalType.STRING, LogicalType.ENUM),
    }
    return (
        (old_type, new_type) not in compatible_pairs
        and (new_type, old_type) not in compatible_pairs
    )


def is_constraint_tightening(old: FieldConstraints, new: FieldConstraints) -> bool:
    """Return True when constraints became stricter."""
    if new.min_value is not None and (old.min_value is None or new.min_value > old.min_value):
        return True
    if new.max_value is not None and (old.max_value is None or new.max_value < old.max_value):
        return True
    if new.min_length is not None and (old.min_length is None or new.min_length > old.min_length):
        return True
    if new.max_length is not None and (old.max_length is None or new.max_length < old.max_length):
        return True
    if new.unique and not old.unique:
        return True
    return bool(
        old.enum_values
        and new.enum_values
        and set(new.enum_values) < set(old.enum_values)
    )


def is_constraint_loosening(old: FieldConstraints, new: FieldConstraints) -> bool:
    """Return True when constraints became looser."""
    if old.min_value is not None and (new.min_value is None or new.min_value < old.min_value):
        return True
    if old.max_value is not None and (new.max_value is None or new.max_value > old.max_value):
        return True
    if old.min_length is not None and (new.min_length is None or new.min_length < old.min_length):
        return True
    if old.max_length is not None and (new.max_length is None or new.max_length > old.max_length):
        return True
    if old.unique and not new.unique:
        return True
    return bool(
        old.enum_values
        and new.enum_values
        and set(new.enum_values) > set(old.enum_values)
    )


def classify_field_change(
    old_field: ContractField,
    new_field: ContractField,
    *,
    mode: CompatibilityMode = CompatibilityMode.BACKWARD,
) -> tuple[list[str], list[str]]:
    """Classify a field change as breaking and/or non-breaking messages."""
    del mode
    breaking: list[str] = []
    non_breaking: list[str] = []

    if is_type_incompatible(old_field.logical_type, new_field.logical_type):
        breaking.append(
            f"Field '{old_field.name}' type changed from {old_field.logical_type.value} "
            f"to {new_field.logical_type.value}"
        )

    if old_field.nullable and not new_field.nullable:
        breaking.append(f"Field '{old_field.name}' changed from nullable to non-nullable")

    if not old_field.required and new_field.required:
        breaking.append(f"Field '{old_field.name}' changed from optional to required")

    if is_constraint_tightening(old_field.constraints, new_field.constraints):
        breaking.append(f"Field '{old_field.name}' constraints were tightened")

    if is_constraint_loosening(old_field.constraints, new_field.constraints):
        non_breaking.append(f"Field '{old_field.name}' constraints were loosened")

    if old_field.description != new_field.description and new_field.description:
        non_breaking.append(f"Field '{old_field.name}' description updated")

    if set(new_field.aliases) > set(old_field.aliases):
        non_breaking.append(f"Field '{old_field.name}' aliases added")

    return breaking, non_breaking


def is_removed_field_breaking(field: ContractField) -> bool:
    """Return True when removing a field is a breaking change."""
    return field.required and not field.nullable
