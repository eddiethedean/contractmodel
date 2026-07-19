"""Tests for bug-audit fixes."""

import urllib.error
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from contractmodel import DataContract
from contractmodel.adapters.odcs import import_odcs, is_odcs_document
from contractmodel.adapters.pydantic import generate_pydantic_model
from contractmodel.core.ccm import CanonicalContract
from contractmodel.errors import OdcsImportError, RegistryError
from contractmodel.examples import example_path, read_example_text
from contractmodel.plugins.manager import clear_plugin_cache, discover_entry_points
from contractmodel.registry.client import fetch_contract, publish_contract
from contractmodel.validation.engine import validate_records
from contractmodel.validation.limits import check_byte_limit, check_file_byte_limit, check_row_limit


def test_example_path_rejects_traversal() -> None:
    with pytest.raises(ValueError, match="Invalid example name"):
        example_path("../pyproject.toml")
    with pytest.raises(ValueError, match="Invalid example name"):
        read_example_text("../../etc/passwd")


def test_examples_absolute_path_rejected() -> None:
    with pytest.raises(ValueError, match="Invalid example name"):
        read_example_text("/etc/passwd")


def test_is_odcs_document_rejects_ccm_with_kind_only() -> None:
    assert is_odcs_document({"kind": "DataContract", "contract_id": "x"}) is False


def test_is_odcs_document_rejects_ccm_even_with_format() -> None:
    doc = {"format": "odcs", "contract_id": "x", "name": "X", "version": "1"}
    assert is_odcs_document(doc) is False


def test_odcs_schema_item_must_be_object() -> None:
    with pytest.raises(OdcsImportError, match="schema item 0"):
        import_odcs(
            {
                "id": "x",
                "name": "X",
                "version": "1.0.0",
                "schema": [None],
            }
        )


def test_odcs_empty_enum_rejected() -> None:
    with pytest.raises(OdcsImportError, match="enum must be non-empty"):
        import_odcs(
            {
                "id": "x",
                "name": "X",
                "version": "1.0.0",
                "schema": [{"name": "status", "logicalType": "string", "enum": []}],
            }
        )


def test_odcs_contact_list_parsed() -> None:
    contract = import_odcs(
        {
            "id": "x",
            "name": "X",
            "version": "1.0.0",
            "owner": {"contact": [{"email": "a@example.com", "name": "Alice"}]},
            "schema": [{"name": "id", "logicalType": "string", "required": True}],
        }
    )
    assert contract.ownership is not None
    assert contract.ownership.contacts[0].email == "a@example.com"
    assert contract.ownership.contacts[0].name == "Alice"


def test_uniqueness_unhashable_values() -> None:
    contract = CanonicalContract.model_validate(
        {
            "contract_id": "obj",
            "name": "Obj",
            "version": "1.0.0",
            "schema": {
                "fields": [
                    {
                        "name": "payload",
                        "logical_type": "object",
                        "constraints": {"unique": True},
                        "children": [{"name": "k", "logical_type": "string"}],
                    }
                ]
            },
        }
    )
    records = [{"payload": {"k": "a"}}, {"payload": {"k": "a"}}]
    result = validate_records(contract, records)
    assert result.success is False
    assert any(error.code == "CM_DATASET_UNIQUE" for error in result.errors)


def test_uniqueness_metrics_count_invalid_rows() -> None:
    contract = CanonicalContract.model_validate(
        {
            "contract_id": "unique",
            "name": "Unique",
            "version": "1.0.0",
            "schema": {
                "fields": [
                    {
                        "name": "id",
                        "logical_type": "string",
                        "constraints": {"unique": True},
                    }
                ]
            },
        }
    )
    result = validate_records(contract, [{"id": "a"}, {"id": "a"}])
    assert result.success is False
    assert result.metrics["records_invalid"] >= 1


def test_validate_json_byte_limit() -> None:
    contract = DataContract.from_ccm(
        CanonicalContract.model_validate(
            {
                "contract_id": "x",
                "name": "X",
                "version": "1.0.0",
                "schema": {"fields": [{"name": "id", "logical_type": "string"}]},
            }
        )
    )
    result = contract.validate_json('{"id": "a"}', max_bytes=5)
    assert result.success is False
    assert result.errors[0].code == "CM_RUNTIME_ERROR"


def test_validate_row_limit() -> None:
    contract = DataContract.from_ccm(
        CanonicalContract.model_validate(
            {
                "contract_id": "x",
                "name": "X",
                "version": "1.0.0",
                "schema": {"fields": [{"name": "id", "logical_type": "string"}]},
            }
        )
    )
    result = contract.validate_records([{"id": "a"}, {"id": "b"}], max_rows=1)
    assert result.success is False
    assert "Record count" in result.errors[0].message


def test_validate_file_byte_limit(tmp_path: Path) -> None:
    contract = DataContract.from_ccm(
        CanonicalContract.model_validate(
            {
                "contract_id": "x",
                "name": "X",
                "version": "1.0.0",
                "schema": {"fields": [{"name": "id", "logical_type": "string"}]},
            }
        )
    )
    data_path = tmp_path / "data.json"
    data_path.write_text('{"id": "a"}', encoding="utf-8")
    result = contract.validate(data_path, max_bytes=5)
    assert result.success is False


def test_pydantic_empty_enum_rejected() -> None:
    contract = CanonicalContract.model_validate(
        {
            "contract_id": "enum",
            "name": "Enum",
            "version": "1.0.0",
            "schema": {
                "fields": [
                    {
                        "name": "status",
                        "logical_type": "enum",
                        "constraints": {"enum_values": []},
                    }
                ]
            },
        }
    )
    with pytest.raises(ValueError, match="enum_values"):
        generate_pydantic_model(contract)


def test_limits_within_bounds(tmp_path: Path) -> None:
    assert check_byte_limit("ok", max_bytes=10) is None
    assert check_byte_limit(b"ok", max_bytes=10) is None
    assert check_byte_limit("ok", max_bytes=None) is None
    data_file = tmp_path / "small.json"
    data_file.write_text('{"id": "a"}', encoding="utf-8")
    assert check_file_byte_limit(data_file, max_bytes=100) is None
    assert check_file_byte_limit(data_file, max_bytes=None) is None
    assert check_row_limit(1, max_rows=10) is None
    assert check_row_limit(1, max_rows=None) is None


def test_publish_contract_http_error() -> None:
    contract = CanonicalContract.model_validate(
        {
            "contract_id": "test",
            "name": "Test",
            "version": "1.0.0",
            "schema": {"fields": [{"name": "id", "logical_type": "string"}]},
        }
    )
    error = urllib.error.HTTPError("http://registry.test", 403, "Forbidden", {}, None)
    with (
        patch("urllib.request.urlopen", side_effect=error),
        pytest.raises(RegistryError, match="status 403"),
    ):
        publish_contract(contract, "http://registry.test")


def test_fetch_contract_http_error() -> None:
    error = urllib.error.HTTPError("http://registry.test", 404, "Not Found", {}, None)
    with (
        patch("urllib.request.urlopen", side_effect=error),
        pytest.raises(RegistryError, match="status 404"),
    ):
        fetch_contract("http://registry.test", "missing")


def test_fetch_contract_response_too_large() -> None:
    response = MagicMock()
    response.read.side_effect = lambda size: b"x" * size
    response.__enter__ = lambda self: self
    response.__exit__ = MagicMock(return_value=False)

    with (
        patch("urllib.request.urlopen", return_value=response),
        pytest.raises(RegistryError, match="exceeds limit"),
    ):
        fetch_contract("http://registry.test", "test")


def test_clear_plugin_cache() -> None:
    clear_plugin_cache()
    entry_point = MagicMock()
    entry_point.name = "cached"
    entry_point.load.return_value = object()
    with patch("contractmodel.plugins.manager.importlib.metadata.entry_points") as mock_eps:
        mock_eps.return_value.select.return_value = [entry_point]
        first = discover_entry_points("contractmodel.test-group")
        second = discover_entry_points("contractmodel.test-group")
    assert first is second
    clear_plugin_cache()
    with patch("contractmodel.plugins.manager.importlib.metadata.entry_points") as mock_eps:
        mock_eps.return_value.select.return_value = [entry_point]
        third = discover_entry_points("contractmodel.test-group")
    assert third is not first
