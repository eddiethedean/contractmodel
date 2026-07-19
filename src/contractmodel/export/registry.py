"""Export target stability classification."""

from __future__ import annotations

from enum import Enum


class ExportStability(str, Enum):
    STABLE = "stable"
    PROVISIONAL = "provisional"
    EXPERIMENTAL = "experimental"
    PRIVATE = "private"


_EXPORT_STABILITY: dict[str, ExportStability] = {
    "odcs": ExportStability.STABLE,
    "ccm": ExportStability.STABLE,
    "ccm_json": ExportStability.STABLE,
    "json_schema": ExportStability.STABLE,
    "markdown": ExportStability.STABLE,
    "openapi": ExportStability.PROVISIONAL,
    "rdf": ExportStability.EXPERIMENTAL,
    "shacl": ExportStability.EXPERIMENTAL,
    "owl": ExportStability.EXPERIMENTAL,
}


def export_stability(target: str) -> ExportStability:
    """Return the stability tier for an export target name."""
    key = target.strip().lower().replace("-", "_")
    return _EXPORT_STABILITY.get(key, ExportStability.PRIVATE)


def known_export_targets() -> dict[str, ExportStability]:
    """Return a copy of the export stability registry."""
    return dict(_EXPORT_STABILITY)
