"""Loading policy and extension budget tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from contractmodel import (
    DataContract,
    ExtensionBudgetError,
    LoadingPolicy,
    LoadingPolicyError,
    OdcsImportError,
)


def test_loading_policy_rejects_path_outside_roots(tmp_path: Path) -> None:
    allowed = tmp_path / "allowed"
    allowed.mkdir()
    outside = tmp_path / "outside.yaml"
    outside.write_text(
        "contract_id: x\nname: X\nversion: 1.0.0\nschema:\n  fields: []\n",
        encoding="utf-8",
    )
    policy = LoadingPolicy(approved_roots=(allowed,))
    with pytest.raises(LoadingPolicyError, match="approved_roots"):
        DataContract.load(outside, policy=policy)


def test_loading_policy_rejects_oversize_file(tmp_path: Path) -> None:
    path = tmp_path / "big.yaml"
    path.write_text("x" * 200, encoding="utf-8")
    policy = LoadingPolicy(max_bytes=50, approved_roots=(tmp_path,))
    with pytest.raises(LoadingPolicyError, match="max_bytes"):
        DataContract.load(path, policy=policy)


def test_unsupported_odcs_version_fails_before_generation() -> None:
    data = {
        "apiVersion": "v9.9.9",
        "kind": "DataContract",
        "id": "x",
        "name": "X",
        "version": "1.0.0",
        "status": "draft",
        "schema": [
            {
                "name": "row",
                "logicalType": "object",
                "properties": [{"name": "id", "logicalType": "string"}],
            }
        ],
    }
    with pytest.raises((OdcsImportError, LoadingPolicyError), match="apiVersion"):
        DataContract.from_odcs_dict(data)


def test_extension_budget_rejects_oversized_payload() -> None:
    data = {
        "apiVersion": "v3.1.0",
        "kind": "DataContract",
        "id": "x",
        "name": "X",
        "version": "1.0.0",
        "status": "draft",
        "schema": [
            {
                "name": "row",
                "logicalType": "object",
                "properties": [{"name": "id", "logicalType": "string"}],
            }
        ],
        "customProperties": [{"property": "x-huge", "value": "y" * 70_000}],
    }
    policy = LoadingPolicy(max_bytes=None, max_collection_size=None)
    with pytest.raises(ExtensionBudgetError, match="max_bytes"):
        DataContract.from_odcs_dict(data, policy=policy)
