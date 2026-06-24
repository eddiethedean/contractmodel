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


def test_from_ccm_preserves_contract_id() -> None:
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


def test_from_dict_ccm_and_odcs() -> None:
    ccm_data = yaml.safe_load((EXAMPLES / "customer_events.ccm.yaml").read_text())
    odcs_data = yaml.safe_load((EXAMPLES / "customer_events.odcs.yaml").read_text())
    assert DataContract.from_dict(ccm_data).contract_id == "customer-events"
    assert DataContract.from_dict(odcs_data).contract_id == "customer-events"


def test_load_alias() -> None:
    contract = DataContract.load(EXAMPLES / "customer_events.ccm.yaml")
    assert contract.name == "Customer Events"


def test_metadata_properties() -> None:
    contract = DataContract.load(EXAMPLES / "customer_events.ccm.yaml")
    assert contract.contract_id == "customer-events"
    assert contract.kind == contract.ccm.kind
    assert contract.status == contract.ccm.status
    assert contract.schema.fields == contract.fields


def test_to_yaml_roundtrip(tmp_path: Path) -> None:
    contract = DataContract.load(EXAMPLES / "customer_events.ccm.yaml")
    out = tmp_path / "out.yaml"
    contract.to_yaml(out)
    assert out.is_file()
    reloaded = DataContract.from_yaml(out)
    assert reloaded.contract_id == contract.contract_id


def test_to_json_roundtrip(tmp_path: Path) -> None:
    contract = DataContract.load(EXAMPLES / "customer_events.ccm.yaml")
    out = tmp_path / "out.json"
    contract.to_json(out)
    reloaded = DataContract.from_json(out)
    assert reloaded.contract_id == contract.contract_id


def test_save_ccm_and_odcs(tmp_path: Path) -> None:
    contract = DataContract.from_odcs(EXAMPLES / "customer_events.odcs.yaml")
    ccm_path = tmp_path / "saved.yaml"
    odcs_path = tmp_path / "saved.odcs.yaml"
    contract.save(ccm_path, format="ccm")
    contract.save(odcs_path, format="odcs")
    assert DataContract.from_yaml(ccm_path).contract_id == "customer-events"
    assert DataContract.from_odcs(odcs_path).contract_id == "customer-events"


def test_validate_file_dispatch(tmp_path: Path) -> None:
    contract = DataContract.from_odcs(EXAMPLES / "customer_events.odcs.yaml")
    data = (EXAMPLES / "data" / "customer_event.json").read_text()
    json_path = tmp_path / "event.json"
    json_path.write_text(data)
    result = contract.validate(json_path)
    assert result.success is True
    assert bool(result) is True


def test_validation_result_raise_for_errors() -> None:
    contract = DataContract.from_odcs(EXAMPLES / "customer_events.odcs.yaml")
    result = contract.validate_record({})
    assert not result
    with pytest.raises(ValueError, match="CM_"):
        result.raise_for_errors()
