"""Tests for JSON validation edge cases."""

import json
from pathlib import Path

from contractmodel import DataContract
from contractmodel.validation.engine import validate_json

EXAMPLE = Path(__file__).resolve().parents[2] / "examples/customer_events.odcs.yaml"


def test_validate_json_invalid_json() -> None:
    contract = DataContract.from_odcs(EXAMPLE)
    result = validate_json(contract.ccm, "{not json")
    assert result.success is False
    assert result.errors[0].code == "CM_RUNTIME_ERROR"


def test_validate_json_non_object_array_items() -> None:
    contract = DataContract.from_odcs(EXAMPLE)
    valid = {
        "event_id": "550e8400-e29b-41d4-a716-446655440000",
        "customer_id": "C1",
        "event_timestamp": "2026-06-23T12:00:00",
        "event_type": "created",
    }
    result = validate_json(contract.ccm, json.dumps([valid, "bad"]))
    assert result.success is False
    runtime = [error for error in result.errors if error.code == "CM_RUNTIME_ERROR"]
    assert len(runtime) == 1
    assert runtime[0].row == 1
    assert "must be objects" in runtime[0].message
    assert result.metrics["records_total"] == 2
