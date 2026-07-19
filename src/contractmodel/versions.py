"""Published version ranges for ODCS and Pydantic."""

from __future__ import annotations

import pyodcs

CCM_WIRE_VERSION = "contractmodel.ccm/1"
CCM_WIRE_SCHEMA_ID = "https://contractmodel.dev/schemas/ccm/1"

# pyodcs.UPSTREAM_SPEC_VERSION is "3.1.0"; ODCS documents use the "v" prefix.
_UPSTREAM = pyodcs.UPSTREAM_SPEC_VERSION
DEFAULT_ODCS_API_VERSION = _UPSTREAM if _UPSTREAM.startswith("v") else f"v{_UPSTREAM}"
SUPPORTED_ODCS_VERSIONS: frozenset[str] = frozenset({DEFAULT_ODCS_API_VERSION})

SUPPORTED_PYDANTIC = ">=2.7,<3"


def normalize_odcs_api_version(value: str | None) -> str | None:
    """Return a normalized ODCS apiVersion or None if absent."""
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def is_supported_odcs_version(value: str | None) -> bool:
    """Return True when apiVersion is in the supported set (required; None is unsupported)."""
    normalized = normalize_odcs_api_version(value)
    if normalized is None:
        return False
    return normalized in SUPPORTED_ODCS_VERSIONS
