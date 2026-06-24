"""Comprehensive tests for diff rules."""

import copy

from contractmodel.core.ccm import ContractField
from contractmodel.core.constraints import FieldConstraints
from contractmodel.core.types import CompatibilityMode, LogicalType
from contractmodel.diff.rules import (
    classify_field_change,
    detect_renames,
    is_added_field_breaking,
    is_constraint_loosening,
    is_constraint_tightening,
    is_removed_field_breaking,
    is_type_incompatible,
)


def _field(**kwargs: object) -> ContractField:
    return ContractField.model_validate({"name": "x", "logical_type": "string", **kwargs})


def test_type_compatible_pairs() -> None:
    assert is_type_incompatible(LogicalType.INTEGER, LogicalType.NUMBER) is False
    assert is_type_incompatible(LogicalType.STRING, LogicalType.ENUM) is False
    assert is_type_incompatible(LogicalType.STRING, LogicalType.INTEGER) is True


def test_constraint_tightening_branches() -> None:
    base = FieldConstraints()
    assert is_constraint_tightening(base, FieldConstraints(min_value=1)) is True
    assert is_constraint_tightening(base, FieldConstraints(max_value=10)) is True
    assert is_constraint_tightening(base, FieldConstraints(min_length=1)) is True
    assert is_constraint_tightening(base, FieldConstraints(max_length=10)) is True
    assert is_constraint_tightening(base, FieldConstraints(unique=True)) is True
    assert is_constraint_tightening(base, FieldConstraints(pattern="^a")) is True
    assert is_constraint_tightening(base, FieldConstraints(immutable=True)) is True
    assert is_constraint_tightening(
        FieldConstraints(allowed_values=["a", "b"]),
        FieldConstraints(allowed_values=["a"]),
    ) is True
    assert is_constraint_tightening(
        FieldConstraints(disallowed_values=["x"]),
        FieldConstraints(disallowed_values=["x", "y"]),
    ) is True
    assert is_constraint_tightening(
        FieldConstraints(enum_values=["a", "b"]),
        FieldConstraints(enum_values=["a"]),
    ) is True
    assert is_constraint_tightening(base, FieldConstraints(enum_values=["a"])) is True
    assert is_constraint_tightening(
        FieldConstraints(enum_values=["a"]),
        FieldConstraints(),
    ) is True


def test_constraint_loosening_branches() -> None:
    tight = FieldConstraints(
        min_value=1,
        max_value=10,
        min_length=1,
        max_length=5,
        unique=True,
        pattern="^a",
        immutable=True,
        enum_values=["a"],
    )
    loose = FieldConstraints(
        min_value=0,
        max_value=20,
        min_length=0,
        max_length=10,
        unique=False,
        pattern=None,
        immutable=False,
        enum_values=["a", "b"],
    )
    assert is_constraint_loosening(tight, loose) is True


def test_constraint_loosening_allowed_and_disallowed_values() -> None:
    assert is_constraint_loosening(
        FieldConstraints(allowed_values=["a"]),
        FieldConstraints(allowed_values=["a", "b"]),
    ) is True
    assert is_constraint_loosening(
        FieldConstraints(disallowed_values=["x", "y"]),
        FieldConstraints(disallowed_values=["x"]),
    ) is True


def test_classify_none_mode() -> None:
    old = _field(name="id", required=False)
    new = _field(name="id", required=True, description="updated")
    breaking, non_breaking = classify_field_change(old, new, mode=CompatibilityMode.NONE)
    assert breaking
    assert not non_breaking


def test_classify_forward_type_change() -> None:
    old = _field(name="id", logical_type=LogicalType.STRING)
    new = _field(name="id", logical_type=LogicalType.INTEGER)
    breaking, _ = classify_field_change(old, new, mode=CompatibilityMode.FORWARD)
    assert not breaking


def test_classify_non_breaking_updates() -> None:
    old = _field(
        name="id",
        required=True,
        nullable=False,
        description="old",
        examples=["a"],
        aliases=[],
        constraints=FieldConstraints(max_value=100),
    )
    new = copy.deepcopy(old)
    new.nullable = True
    new.required = False
    new.description = "new"
    new.examples = ["a", "b"]
    new.aliases = ["identifier"]
    new.semantic = {"iri": "urn:id"}
    new.constraints = FieldConstraints(max_value=200)
    _, non_breaking = classify_field_change(old, new)
    assert len(non_breaking) >= 4


def test_removed_field_modes() -> None:
    field = _field(name="id", required=True, nullable=False)
    assert is_removed_field_breaking(field, mode=CompatibilityMode.BACKWARD) is True
    assert is_removed_field_breaking(field, mode=CompatibilityMode.FORWARD) is False
    assert is_removed_field_breaking(field, mode=CompatibilityMode.NONE) is True


def test_added_field_full_mode() -> None:
    field = _field(name="id", required=True, nullable=False)
    assert is_added_field_breaking(field, mode=CompatibilityMode.FULL) is True
    optional = _field(name="id", required=False, nullable=True)
    assert is_added_field_breaking(optional, mode=CompatibilityMode.BACKWARD) is False


def test_detect_renames() -> None:
    removed = {
        "old_name": _field(name="old_name", aliases=["new_name"]),
    }
    added = {
        "new_name": _field(name="new_name", aliases=["old_name"]),
    }
    paired_removed, paired_added, messages = detect_renames(removed, added)
    assert "old_name" in paired_removed
    assert "new_name" in paired_added
    assert messages
