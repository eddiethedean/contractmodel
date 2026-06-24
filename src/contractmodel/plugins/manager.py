"""Plugin discovery and management."""

from __future__ import annotations

import importlib.metadata
from functools import lru_cache
from typing import Any, cast

from contractmodel.errors import ContractPluginError


def list_plugin_names(group: str) -> list[str]:
    """Return entry point names for a group without importing plugin modules."""
    try:
        entry_points = importlib.metadata.entry_points()
        if hasattr(entry_points, "select"):
            selected = entry_points.select(group=group)
        else:
            selected = cast(Any, entry_points).get(group, [])
        return sorted(ep.name for ep in selected)
    except Exception:
        return []


@lru_cache(maxsize=16)
def discover_entry_points(group: str) -> dict[str, Any]:
    """Discover and load plugins for an entry point group."""
    plugins: dict[str, Any] = {}
    try:
        entry_points = importlib.metadata.entry_points()
        if hasattr(entry_points, "select"):
            selected = entry_points.select(group=group)
        else:
            selected = cast(Any, entry_points).get(group, [])
        for entry_point in selected:
            try:
                plugins[entry_point.name] = entry_point.load()
            except Exception as exc:
                raise ContractPluginError(
                    f"Failed to load plugin '{entry_point.name}' in group '{group}'"
                ) from exc
    except ContractPluginError:
        raise
    except Exception:
        return plugins
    return plugins


def clear_plugin_cache() -> None:
    """Clear cached plugin entry points (mainly for tests)."""
    discover_entry_points.cache_clear()
