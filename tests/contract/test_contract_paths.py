"""Tests for contract facade edge cases."""

import json
from pathlib import Path

import pytest
import yaml

from contractmodel import DataContract
from contractmodel.core.ccm import CanonicalContract

EXAMPLES = Path(__file__).resolve().parents[2] / "examples"


def test_from_yaml_invalid_mapping(tmp_path: Path) -> None:
    path = tmp_path / "bad.yaml"
    path.write_text("- not a mapping\n")
    with pytest.raises(ValueError, match="mapping"):
        DataContract.from_yaml(path)


def test_from_json_invalid_object(tmp_path: Path) -> None:
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(["not", "object"]))
    with pytest.raises(ValueError, match="object"):
        DataContract.from_json(path)


def test_from_json_ccm_direct(tmp_path: Path) -> None:
    data = yaml.safe_load((EXAMPLES / "customer_events.ccm.yaml").read_text())
    path = tmp_path / "contract.json"
    path.write_text(json.dumps(data))
    contract = DataContract.from_json(path)
    assert contract.ccm.contract_id == "customer-events"


def test_from_odcs_invalid(tmp_path: Path) -> None:
    path = tmp_path / "bad.yaml"
    path.write_text("[]\n")
    with pytest.raises(ValueError, match="mapping"):
        DataContract.from_odcs(path)


def test_from_ccm_and_import_warnings() -> None:
    ccm = CanonicalContract.model_validate(
        {
            "contract_id": "warn",
            "name": "Warn",
            "version": "1.0.0",
            "schema": {"fields": [{"name": "id", "logical_type": "string"}]},
        }
    )
    contract = DataContract.from_ccm(ccm)
    assert contract.ccm.contract_id == "warn"


def test_from_odcs_dict_with_contact_warning() -> None:
    data = {
        "apiVersion": "v3.0.0",
        "kind": "DataContract",
        "id": "warn",
        "name": "Warn",
        "version": "1.0.0",
        "owner": {"contact": [{"email": "a@example.com"}]},
        "schema": [{"name": "id", "logicalType": "string", "required": True}],
    }
    contract = DataContract.from_odcs_dict(data)
    assert any(w.code == "ODCS_LOSSY_IMPORT" for w in contract.import_warnings)


def test_validate_methods() -> None:
    contract = DataContract.from_odcs(EXAMPLES / "customer_events.odcs.yaml")
    record = {
        "event_id": "550e8400-e29b-41d4-a716-446655440000",
        "customer_id": "C123",
        "event_timestamp": "2026-06-23T12:00:00",
        "event_type": "created",
    }
    assert contract.validate_record(record).success is True
    assert contract.validate_records([record]).success is True
