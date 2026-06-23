"""Tests for plugin manager."""

from contractmodel.plugins.manager import list_plugins


def test_list_plugins_returns_groups() -> None:
    plugins = list_plugins()
    assert "validators" in plugins
    assert "exporters" in plugins
    assert "registries" in plugins
