"""Tests for 0.1.2 patch audit fixes."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from pydantic import BaseModel, Field

from contractmodel import DataContract
from contractmodel.adapters.odcs import import_odcs
from contractmodel.adapters.pydantic import contract_from_pydantic
from contractmodel.core.ccm import CanonicalContract
from contractmodel.core.types import CompatibilityMode, ValidationMode
from contractmodel.diff.engine import diff_contracts
from contractmodel.errors import ContractPluginError, OdcsImportError, RegistryError
from contractmodel.examples import list_examples, read_example_text
from contractmodel.plugins.runtime import run_exporter_plugin, run_registry_publish
from contractmodel.registry.client import fetch_contract
from contractmodel.validation.engine import validate_json
from contractmodel.validation.limits import validate_limit_params


def test_contract_from_pydantic_preserves_zero_constraints() -> None:
    class ScoreModel(BaseModel):
        score: int = Field(ge=0)
        label: str = Field(min_length=0)

    contract = contract_from_pydantic(ScoreModel)
    score_field = contract.contract_schema.fields[0]
    label_field = contract.contract_schema.fields[1]
    assert score_field.constraints.min_value == 0
    assert label_field.constraints.min_length == 0


def test_permissive_allows_nested_object_extra_fields() -> None:
    contract = CanonicalContract.model_validate(
        {
            "contract_id": "nested",
            "name": "Nested",
            "version": "1.0.0",
            "schema": {
                "fields": [
                    {
                        "name": "payload",
                        "logical_type": "object",
                        "children": [{"name": "city", "logical_type": "string"}],
                    }
                ]
            },
        }
    )
    wrapper = DataContract.from_ccm(contract)
    result = wrapper.validate_record(
        {"payload": {"city": "Boston", "extra": "ignored"}},
        mode=ValidationMode.PERMISSIVE,
    )
    assert result.success is True


def test_validate_json_array_preserves_row_indices() -> None:
    contract = CanonicalContract.model_validate(
        {
            "contract_id": "x",
            "name": "X",
            "version": "1.0.0",
            "schema": {
                "fields": [
                    {
                        "name": "id",
                        "logical_type": "string",
                        "required": True,
                    }
                ]
            },
        }
    )
    result = validate_json(
        contract,
        '[{"id": "a"}, "bad", {"id": null}]',
    )
    assert result.success is False
    assert result.metrics["records_total"] == 3
    assert result.metrics["records_invalid"] >= 2
    rows = {error.row for error in result.errors if error.row is not None}
    assert 1 in rows
    assert 2 in rows


def test_odcs_bool_coercion() -> None:
    contract = import_odcs(
        {
            "id": "x",
            "name": "X",
            "version": "1.0.0",
            "schema": [
                {
                    "name": "flag",
                    "logicalType": "boolean",
                    "required": "false",
                    "unique": "false",
                }
            ],
        }
    )
    field = contract.contract_schema.fields[0]
    assert field.required is False
    assert field.constraints.unique is False


def test_odcs_invalid_bool_raises() -> None:
    with pytest.raises(OdcsImportError, match="Invalid boolean"):
        import_odcs(
            {
                "id": "x",
                "name": "X",
                "version": "1.0.0",
                "schema": [{"name": "flag", "logicalType": "boolean", "required": "maybe"}],
            }
        )


def test_rename_with_type_change_is_breaking() -> None:
    source = CanonicalContract.model_validate(
        {
            "contract_id": "x",
            "name": "X",
            "version": "1.0.0",
            "schema": {
                "fields": [
                    {
                        "name": "customer_id",
                        "logical_type": "string",
                        "aliases": ["client_id"],
                    }
                ]
            },
        }
    )
    target = CanonicalContract.model_validate(
        {
            "contract_id": "x",
            "name": "X",
            "version": "2.0.0",
            "schema": {
                "fields": [
                    {
                        "name": "client_id",
                        "logical_type": "integer",
                        "aliases": ["customer_id"],
                    }
                ]
            },
        }
    )
    diff = diff_contracts(source, target, mode=CompatibilityMode.BACKWARD)
    assert diff.is_breaking
    assert any(change.code == "FIELD_CHANGED" for change in diff.breaking_changes)


def test_validate_limit_params_reject_non_positive() -> None:
    with pytest.raises(ValueError, match="max_bytes"):
        validate_limit_params(max_bytes=0)
    with pytest.raises(ValueError, match="max_rows"):
        validate_limit_params(max_rows=-1)


def test_validate_missing_file_returns_result(tmp_path: Path) -> None:
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
    missing = tmp_path / "missing.json"
    result = contract.validate(missing)
    assert result.success is False
    assert result.errors[0].code == "CM_RUNTIME_ERROR"


def test_run_registry_publish_forwards_url() -> None:
    contract = CanonicalContract.model_validate(
        {
            "contract_id": "x",
            "name": "X",
            "version": "1.0.0",
            "schema": {"fields": []},
        }
    )
    plugin = MagicMock()
    plugin.publish.return_value = {"ok": True}
    with patch(
        "contractmodel.plugins.runtime.discover_entry_points",
        return_value={"hub": plugin},
    ):
        run_registry_publish(contract, "http://registry.test")
    plugin.publish.assert_called_once_with(contract, "http://registry.test")


def test_exporter_plugin_none_raises() -> None:
    contract = CanonicalContract.model_validate(
        {
            "contract_id": "x",
            "name": "X",
            "version": "1.0.0",
            "schema": {"fields": []},
        }
    )
    plugin = MagicMock()
    plugin.target = "custom"
    plugin.export.return_value = None
    with patch(
        "contractmodel.plugins.runtime.discover_entry_points",
        return_value={"custom": plugin},
    ), pytest.raises(ContractPluginError, match="returned no content"):
        run_exporter_plugin(contract, "custom")


def test_fetch_contract_invalid_json() -> None:
    response = MagicMock()
    response.read.side_effect = [b"not-json", b""]
    response.__enter__ = lambda self: self
    response.__exit__ = MagicMock(return_value=False)
    with (
        patch("urllib.request.urlopen", return_value=response),
        pytest.raises(RegistryError, match="invalid JSON"),
    ):
        fetch_contract("http://registry.test", "test")


def test_unknown_example_raises_value_error() -> None:
    with pytest.raises(ValueError, match="Unknown example"):
        read_example_text("does-not-exist.ccm.yaml")


def test_list_examples_matches_bundle() -> None:
    names = list_examples()
    assert "customer_events.ccm.yaml" in names
    assert "data/customer_event.json" in names


def test_uniqueness_counts_all_duplicate_rows() -> None:
    from contractmodel.validation.engine import validate_records

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
    result = validate_records(contract, [{"id": "a"}, {"id": "a"}, {"id": "a"}])
    assert result.success is False
    assert result.metrics["records_invalid"] >= 2


def test_validate_json_rejects_scalar() -> None:
    contract = CanonicalContract.model_validate(
        {
            "contract_id": "x",
            "name": "X",
            "version": "1.0.0",
            "schema": {"fields": [{"name": "id", "logical_type": "string"}]},
        }
    )
    result = validate_json(contract, "42")
    assert result.success is False
    assert result.metrics["records_total"] == 0


def test_odcs_nullable_coercion() -> None:
    contract = import_odcs(
        {
            "id": "x",
            "name": "X",
            "version": "1.0.0",
            "schema": [{"name": "id", "logicalType": "string", "nullable": "true"}],
        }
    )
    assert contract.contract_schema.fields[0].nullable is True


def test_registry_plugin_legacy_publish_signature() -> None:
    contract = CanonicalContract.model_validate(
        {
            "contract_id": "x",
            "name": "X",
            "version": "1.0.0",
            "schema": {"fields": []},
        }
    )
    plugin = MagicMock()
    plugin.publish.side_effect = [TypeError("legacy"), {"ok": True}]
    with patch(
        "contractmodel.plugins.runtime.discover_entry_points",
        return_value={"legacy": plugin},
    ):
        result = run_registry_publish(contract, "http://registry.test")
    assert result == {"ok": True}
    assert plugin.publish.call_count == 2
