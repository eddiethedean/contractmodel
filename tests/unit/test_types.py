"""Tests for core type enumerations."""

import enum

import pytest

from contractmodel.core.types import (
    CompatibilityMode,
    ContractKind,
    ContractStatus,
    LogicalType,
    ValidationMode,
)


@pytest.mark.parametrize(
    ("enum_cls", "expected_count"),
    [
        (ContractKind, 7),
        (ContractStatus, 4),
        (LogicalType, 18),
        (ValidationMode, 4),
        (CompatibilityMode, 4),
    ],
)
def test_enum_members_are_complete(enum_cls: type[enum.Enum], expected_count: int) -> None:
    assert len(enum_cls) == expected_count
    assert all(isinstance(member.value, str) for member in enum_cls)
