"""Published version ranges for ODCS and Pydantic."""

from __future__ import annotations

CCM_WIRE_VERSION = "contractmodel.ccm/1"
CCM_WIRE_SCHEMA_ID = "https://contractmodel.dev/schemas/ccm/1"

# ODCS apiVersion values accepted on import / loading policy.
SUPPORTED_ODCS_VERSIONS: frozenset[str] = frozenset({"v3.0.0", "v3.1.0"})
DEFAULT_ODCS_API_VERSION = "v3.1.0"

SUPPORTED_PYDANTIC = ">=2.7,<3"


def normalize_odcs_api_version(value: str | None) -> str | None:
    """Return a normalized ODCS apiVersion or None if absent."""
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def is_supported_odcs_version(value: str | None) -> bool:
    """Return True when apiVersion is missing (legacy) or in the supported set."""
    normalized = normalize_odcs_api_version(value)
    if normalized is None:
        return True
    return normalized in SUPPORTED_ODCS_VERSIONS
