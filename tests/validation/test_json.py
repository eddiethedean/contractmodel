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
    result = validate_json(contract.ccm, json.dumps([{"event_id": "x"}, "bad"]))
    assert result.success is False
    assert any(error.code == "CM_RUNTIME_ERROR" for error in result.errors)
