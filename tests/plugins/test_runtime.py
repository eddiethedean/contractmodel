"""Tests for plugin runtime dispatch."""

from unittest.mock import MagicMock, patch

import pytest

from contractmodel.core.ccm import CanonicalContract
from contractmodel.core.result import ValidationErrorDetail, ValidationResult
from contractmodel.errors import ContractPluginError
from contractmodel.plugins.runtime import (
    list_plugins,
    run_exporter_plugin,
    run_validator_plugins,
)


def test_list_plugins_does_not_load_modules() -> None:
    with patch(
        "contractmodel.plugins.runtime.list_plugin_names",
        return_value=["my-validator"],
    ):
        plugins = list_plugins()
    assert plugins["validators"] == ["my-validator"]


def test_run_validator_plugins_merges_results() -> None:
    contract = CanonicalContract.model_validate(
        {
            "contract_id": "x",
            "name": "X",
            "version": "1.0.0",
            "schema": {"fields": [{"name": "id", "logical_type": "string"}]},
        }
    )
    base = ValidationResult(success=True, errors=[], warnings=[])
    plugin = MagicMock()
    plugin.validate.return_value = ValidationResult(
        success=False,
        error_count=1,
        errors=[
            ValidationErrorDetail(
                code="PLUGIN_ERROR",
                message="Plugin rejected data",
                field="id",
            )
        ],
    )
    with patch(
        "contractmodel.plugins.runtime.discover_entry_points",
        return_value={"extra": plugin},
    ):
        result = run_validator_plugins(contract, {"id": "1"}, base)
    assert result.success is False
    assert any(error.code == "PLUGIN_ERROR" for error in result.errors)


def test_run_exporter_plugin_returns_matching_target() -> None:
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
    plugin.export.return_value = {"ok": True}
    with patch(
        "contractmodel.plugins.runtime.discover_entry_points",
        return_value={"custom": plugin},
    ):
        content = run_exporter_plugin(contract, "custom")
    assert content == {"ok": True}


def test_run_validator_plugins_raises_contract_plugin_error() -> None:
    contract = CanonicalContract.model_validate(
        {
            "contract_id": "x",
            "name": "X",
            "version": "1.0.0",
            "schema": {"fields": []},
        }
    )
    plugin = MagicMock()
    plugin.validate.side_effect = RuntimeError("boom")
    with (
        patch(
            "contractmodel.plugins.runtime.discover_entry_points",
            return_value={"bad": plugin},
        ),
        pytest.raises(ContractPluginError, match="Validator plugin 'bad' failed"),
    ):
        run_validator_plugins(contract, {}, ValidationResult(success=True))
