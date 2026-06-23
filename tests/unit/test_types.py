"""Tests for core type enumerations."""

from contractmodel.core.types import (
    CompatibilityMode,
    ContractKind,
    ContractStatus,
    LogicalType,
    ValidationMode,
)


def test_contract_kind_values() -> None:
    assert ContractKind.DATASET.value == "dataset"
    assert ContractKind.API_PAYLOAD.value == "api_payload"


def test_contract_status_values() -> None:
    assert ContractStatus.DRAFT.value == "draft"
    assert ContractStatus.ACTIVE.value == "active"


def test_logical_type_values() -> None:
    assert LogicalType.STRING.value == "string"
    assert LogicalType.UUID.value == "uuid"
    assert LogicalType.ENUM.value == "enum"


def test_validation_mode_values() -> None:
    assert ValidationMode.STRICT.value == "strict"
    assert ValidationMode.SCHEMA_ONLY.value == "schema_only"


def test_compatibility_mode_values() -> None:
    assert CompatibilityMode.BACKWARD.value == "backward"
    assert CompatibilityMode.FULL.value == "full"
