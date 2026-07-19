"""CCM wire serialization helpers for contractmodel.ccm/1."""

from __future__ import annotations

import json
from importlib import resources
from typing import Any

from contractmodel.canonical import canonicalize_jsonable
from contractmodel.core.ccm import CanonicalContract
from contractmodel.versions import CCM_WIRE_VERSION


def _jsonable(value: Any) -> Any:
    return canonicalize_jsonable(value, sort_object_keys=False, numbers_as_strings=False)


def canonical_ccm_dict(contract: CanonicalContract) -> dict[str, Any]:
    """Emit a wire-shaped CCM dict (``schema`` key, enum values as strings)."""
    dumped = contract.model_dump(mode="python", by_alias=True)
    wire = _jsonable(dumped)
    if not isinstance(wire, dict):
        msg = "Canonical contract wire form must be an object"
        raise TypeError(msg)
    wire["ccm_wire_version"] = CCM_WIRE_VERSION
    return wire


def load_ccm_json_schema() -> dict[str, Any]:
    """Load the published ``contractmodel.ccm/1`` JSON Schema document."""
    package = resources.files("contractmodel.schemas.ccm.v1")
    raw = package.joinpath("schema.json").read_text(encoding="utf-8")
    data = json.loads(raw)
    if not isinstance(data, dict):
        msg = "CCM JSON Schema must be an object"
        raise TypeError(msg)
    return data


def export_ccm_json_schema() -> dict[str, Any]:
    """Return a copy of the published CCM wire JSON Schema."""
    copied: dict[str, Any] = json.loads(json.dumps(load_ccm_json_schema()))
    return copied


def ccm_json_schema_text() -> str:
    """Return the packaged CCM JSON Schema document as UTF-8 text."""
    package = resources.files("contractmodel.schemas.ccm.v1")
    return package.joinpath("schema.json").read_text(encoding="utf-8")
