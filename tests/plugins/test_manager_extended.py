"""Extended plugin manager tests."""

from unittest.mock import MagicMock, patch

import pytest

from contractmodel.errors import ContractPluginError
from contractmodel.plugins import protocols
from contractmodel.plugins.manager import (
    clear_plugin_cache,
    discover_entry_points,
    list_plugin_names,
)
from contractmodel.plugins.runtime import list_plugins


@pytest.fixture(autouse=True)
def _clear_plugin_cache() -> None:
    clear_plugin_cache()
    yield
    clear_plugin_cache()


def test_protocols_importable() -> None:
    assert protocols.ValidatorPlugin is not None
    assert protocols.ExporterPlugin is not None


def test_discover_entry_points_load_failure() -> None:
    entry_point = MagicMock()
    entry_point.name = "broken"
    entry_point.load.side_effect = RuntimeError("boom")
    selected = [entry_point]

    with patch("contractmodel.plugins.manager.importlib.metadata.entry_points") as mock_eps:
        mock_eps.return_value.select.return_value = selected
        with pytest.raises(ContractPluginError):
            discover_entry_points("contractmodel.validators")


def test_discover_entry_points_legacy_api() -> None:
    entry_point = MagicMock()
    entry_point.name = "ok"
    entry_point.load.return_value = object()

    class LegacyEntryPoints:
        def get(self, group: str, default: list[MagicMock] | None = None) -> list[MagicMock]:
            return [entry_point]

    with patch(
        "contractmodel.plugins.manager.importlib.metadata.entry_points",
        return_value=LegacyEntryPoints(),
    ):
        plugins = discover_entry_points("contractmodel.validators")
    assert "ok" in plugins


def test_list_plugins_groups() -> None:
    with patch(
        "contractmodel.plugins.runtime.list_plugin_names",
        side_effect=lambda group: ["a"] if "validators" in group else [],
    ):
        plugins = list_plugins()
    assert set(plugins) == {"validators", "exporters", "registries"}
    assert plugins["validators"] == ["a"]


def test_list_plugin_names_without_loading() -> None:
    entry_point = MagicMock()
    entry_point.name = "listed"
    with patch("contractmodel.plugins.manager.importlib.metadata.entry_points") as mock_eps:
        mock_eps.return_value.select.return_value = [entry_point]
        names = list_plugin_names("contractmodel.validators")
    assert names == ["listed"]


def test_list_plugin_names_legacy_api() -> None:
    entry_point = MagicMock()
    entry_point.name = "legacy"

    class LegacyEntryPoints:
        def get(self, group: str, default: list[MagicMock] | None = None) -> list[MagicMock]:
            return [entry_point]

    with patch(
        "contractmodel.plugins.manager.importlib.metadata.entry_points",
        return_value=LegacyEntryPoints(),
    ):
        names = list_plugin_names("contractmodel.validators")
    assert names == ["legacy"]


def test_discover_entry_points_outer_failure() -> None:
    with patch(
        "contractmodel.plugins.manager.importlib.metadata.entry_points",
        side_effect=RuntimeError("metadata unavailable"),
    ):
        plugins = discover_entry_points("contractmodel.validators")
    assert plugins == {}

