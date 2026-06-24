"""Tests for ODCS document detection and facade routing."""

import json
from pathlib import Path

import pytest
import yaml

from contractmodel import DataContract
from contractmodel.adapters.odcs import is_odcs_document


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        ({"kind": "DataContract", "contract_id": "x"}, True),
        ({"apiVersion": "v3.0.0", "name": "n"}, True),
        ({"contract_id": "x", "apiVersion": "v3.0.0"}, False),
        ({"contract_id": "x", "name": "X", "version": "1.0.0"}, False),
    ],
)
def test_is_odcs_document(data: dict, expected: bool) -> None:
    assert is_odcs_document(data) is expected


@pytest.mark.parametrize("suffix", [".yaml", ".json"])
def test_loader_auto_detects_odcs(tmp_path: Path, suffix: str) -> None:
    odcs = {
        "apiVersion": "v3.0.0",
        "kind": "DataContract",
        "id": "x",
        "name": "X",
        "version": "1.0.0",
        "schema": [{"name": "id", "logicalType": "string", "required": True}],
    }
    path = tmp_path / f"contract{suffix}"
    if suffix == ".yaml":
        path.write_text(yaml.dump(odcs))
        contract = DataContract.from_yaml(path)
    else:
        path.write_text(json.dumps(odcs))
        contract = DataContract.from_json(path)
    assert contract.ccm.contract_id == "x"
