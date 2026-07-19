"""Tests for ODCS document detection and facade routing."""

import json
from pathlib import Path

import pytest
import yaml

from contractmodel import DataContract
from contractmodel.adapters.odcs import is_odcs_document
from contractmodel.errors import OdcsValidationError

_VALID_SCHEMA = [
    {
        "name": "row",
        "logicalType": "object",
        "properties": [{"name": "id", "logicalType": "string", "required": True}],
    }
]


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        ({"format": "odcs", "contract_id": "x", "name": "X", "version": "1"}, False),
        (
            {
                "format": "odcs",
                "id": "x",
                "name": "X",
                "version": "1",
                "schema": [],
            },
            True,
        ),
        (
            {
                "apiVersion": "v3.1.0",
                "id": "x",
                "name": "n",
                "version": "1.0.0",
                "schema": [],
            },
            True,
        ),
        (
            {
                "kind": "DataContract",
                "id": "x",
                "name": "n",
                "version": "1.0.0",
                "schema": [],
            },
            True,
        ),
        ({"kind": "DataContract", "contract_id": "x"}, False),
        ({"apiVersion": "v3.1.0", "name": "n"}, False),
        ({"contract_id": "x", "apiVersion": "v3.1.0"}, False),
        ({"contract_id": "x", "name": "X", "version": "1.0.0"}, False),
    ],
)
def test_is_odcs_document(data: dict, expected: bool) -> None:
    assert is_odcs_document(data) is expected


@pytest.mark.parametrize("suffix", [".yaml", ".json"])
def test_loader_auto_detects_odcs(tmp_path: Path, suffix: str) -> None:
    odcs = {
        "apiVersion": "v3.1.0",
        "kind": "DataContract",
        "id": "x",
        "name": "X",
        "version": "1.0.0",
        "status": "draft",
        "schema": _VALID_SCHEMA,
    }
    path = tmp_path / f"contract{suffix}"
    if suffix == ".yaml":
        path.write_text(yaml.dump(odcs))
        contract = DataContract.from_yaml(path)
    else:
        path.write_text(json.dumps(odcs))
        contract = DataContract.from_json(path)
    assert contract.ccm.contract_id == "x"


def test_loader_rejects_unsupported_odcs_version(tmp_path: Path) -> None:
    odcs = {
        "apiVersion": "v3.0.0",
        "kind": "DataContract",
        "id": "x",
        "name": "X",
        "version": "1.0.0",
        "status": "draft",
        "schema": _VALID_SCHEMA,
    }
    path = tmp_path / "contract.yaml"
    path.write_text(yaml.dump(odcs))
    with pytest.raises((OdcsValidationError, Exception)):
        DataContract.from_yaml(path)
