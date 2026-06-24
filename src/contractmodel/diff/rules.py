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
    if new.pattern and not old.pattern:
        return True
    if new.immutable and not old.immutable:
        return True
    if new.allowed_values and (
        not old.allowed_values or set(new.allowed_values) < set(old.allowed_values)
    ):
        return True
    if new.disallowed_values and (
        not old.disallowed_values or set(new.disallowed_values) > set(old.disallowed_values)
    ):
        return True
    if old.enum_values and not new.enum_values:
        return True
    if old.enum_values and new.enum_values and set(new.enum_values) < set(old.enum_values):
        return True
    return bool(not old.enum_values and new.enum_values)


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
    if old.pattern and not new.pattern:
        return True
    if old.immutable and not new.immutable:
        return True
    if old.allowed_values and (
        not new.allowed_values or set(new.allowed_values) > set(old.allowed_values)
    ):
        return True
    if old.disallowed_values and (
        not new.disallowed_values or set(new.disallowed_values) < set(old.disallowed_values)
    ):
        return True
    return bool(old.enum_values and new.enum_values and set(new.enum_values) > set(old.enum_values))


def classify_field_change(
    old_field: ContractField,
    new_field: ContractField,
    *,
    mode: CompatibilityMode = CompatibilityMode.BACKWARD,
) -> tuple[list[str], list[str]]:
    """Classify a field change as breaking and/or non-breaking messages."""
    breaking: list[str] = []
    non_breaking: list[str] = []

    if mode == CompatibilityMode.NONE:
        if old_field != new_field:
            breaking.append(f"Field '{old_field.name}' changed")
        return breaking, non_breaking

    type_changed = is_type_incompatible(old_field.logical_type, new_field.logical_type)
    if type_changed and mode != CompatibilityMode.FORWARD:
        breaking.append(
            f"Field '{old_field.name}' type changed from {old_field.logical_type.value} "
            f"to {new_field.logical_type.value}"
        )

    if old_field.nullable and not new_field.nullable:
        breaking.append(f"Field '{old_field.name}' changed from nullable to non-nullable")

    if not old_field.required and new_field.required:
        breaking.append(f"Field '{old_field.name}' changed from optional to required")

    if not old_field.nullable and new_field.nullable:
        non_breaking.append(f"Field '{old_field.name}' changed from non-nullable to nullable")

    if old_field.required and not new_field.required:
        non_breaking.append(f"Field '{old_field.name}' changed from required to optional")

    if is_constraint_tightening(old_field.constraints, new_field.constraints):
        breaking.append(f"Field '{old_field.name}' constraints were tightened")

    if is_constraint_loosening(old_field.constraints, new_field.constraints):
        non_breaking.append(f"Field '{old_field.name}' constraints were loosened")

    if old_field.description != new_field.description and new_field.description:
        non_breaking.append(f"Field '{old_field.name}' description updated")

    if set(new_field.examples) > set(old_field.examples):
        non_breaking.append(f"Field '{old_field.name}' examples added")

    if set(new_field.aliases) > set(old_field.aliases):
        non_breaking.append(f"Field '{old_field.name}' aliases added")

    if new_field.semantic and not old_field.semantic:
        non_breaking.append(f"Field '{old_field.name}' semantic mapping added")

    return breaking, non_breaking


def is_removed_field_breaking(field: ContractField, *, mode: CompatibilityMode) -> bool:
    """Return True when removing a field is a breaking change."""
    if mode == CompatibilityMode.NONE:
        return True
    return field.required and not field.nullable


def is_added_field_breaking(field: ContractField, *, mode: CompatibilityMode) -> bool:
    """Return True when adding a field is a breaking change."""
    if mode == CompatibilityMode.NONE:
        return True
    if mode == CompatibilityMode.FORWARD:
        return field.required and not field.nullable
    if mode == CompatibilityMode.BACKWARD:
        return field.required and not field.nullable
    if mode == CompatibilityMode.FULL:
        return field.required and not field.nullable
    return False


def detect_renames(
    removed: dict[str, ContractField],
    added: dict[str, ContractField],
) -> tuple[set[str], set[str], list[tuple[str, str, ContractField, ContractField]]]:
    """Pair removed/added fields by aliases.

    Returns paired removed names, paired added names, and rename tuples
    ``(old_name, new_name, old_field, new_field)``.
    """
    paired_removed: set[str] = set()
    paired_added: set[str] = set()
    rename_pairs: list[tuple[str, str, ContractField, ContractField]] = []

    for old_name, old_field in removed.items():
        for new_name, new_field in added.items():
            if new_name in paired_added:
                continue
            old_aliases = set(old_field.aliases)
            new_aliases = set(new_field.aliases)
            if new_name in old_aliases or old_name in new_aliases:
                paired_removed.add(old_name)
                paired_added.add(new_name)
                rename_pairs.append((old_name, new_name, old_field, new_field))
                break

    return paired_removed, paired_added, rename_pairs
