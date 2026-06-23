"""Tests for validation engine."""

from pathlib import Path

from contractmodel import DataContract

EXAMPLES_DIR = Path(__file__).resolve().parents[2] / "examples"


def _contract() -> DataContract:
    return DataContract.from_odcs(EXAMPLES_DIR / "customer_events.odcs.yaml")


def _valid_record() -> dict:
    return {
        "event_id": "550e8400-e29b-41d4-a716-446655440000",
        "customer_id": "C123",
        "event_timestamp": "2026-06-23T12:00:00",
        "event_type": "created",
    }


def test_validate_record_success() -> None:
    result = _contract().validate_record(_valid_record())
    assert result.success is True
    assert result.error_count == 0


def test_validate_record_missing_field() -> None:
    record = _valid_record()
    del record["customer_id"]
    result = _contract().validate_record(record)
    assert result.success is False
    assert any(error.code == "CM_SCHEMA_MISSING_FIELD" for error in result.errors)


def test_validate_record_extra_field_strict() -> None:
    record = _valid_record()
    record["extra"] = "value"
    result = _contract().validate_record(record)
    assert result.success is False
    assert any(error.code == "CM_SCHEMA_EXTRA_FIELD" for error in result.errors)


def test_validate_record_invalid_type() -> None:
    record = _valid_record()
    record["customer_id"] = 123
    result = _contract().validate_record(record)
    assert result.success is False
    assert any(error.code == "CM_TYPE_INVALID" for error in result.errors)


def test_validate_records_batch_metrics() -> None:
    contract = _contract()
    result = contract.validate_records([_valid_record(), {"event_id": "bad"}])
    assert result.success is False
    assert result.metrics["records_total"] == 2
    assert result.metrics["records_invalid"] == 1


def test_validate_json_list() -> None:
    contract = _contract()
    result = contract.validate_json([_valid_record(), _valid_record()])
    assert result.success is True
    assert result.metrics["records_total"] == 2
