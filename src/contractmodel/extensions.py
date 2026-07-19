"""Extension namespace rules and size budgets."""

from __future__ import annotations

import json
import re
from typing import Any

from contractmodel.errors import ContractModelError

# Namespaces that participate in fingerprints when present under extensions.
FINGERPRINT_EXTENSION_NAMESPACES: frozenset[str] = frozenset(
    {
        "apiVersion",
        "kind",
        "format",
    }
)

_VENDOR_KEY = re.compile(r"^[A-Za-z][A-Za-z0-9_]*(\.[A-Za-z][A-Za-z0-9_]*)+$")
_X_PREFIX = re.compile(r"^x-[A-Za-z0-9][A-Za-z0-9_-]*$")

DEFAULT_MAX_EXTENSION_BYTES = 65_536
DEFAULT_MAX_EXTENSION_DEPTH = 8
DEFAULT_MAX_EXTENSION_KEYS = 256


class ExtensionBudgetError(ContractModelError):
    """Raised when extensions exceed size, depth, or key budgets."""


# Extensions may use ODCS leftover keys, ``x-*`` prefixes, or dotted vendor keys.
# All keys must be non-empty strings without control characters; size/depth/key
# budgets are always enforced. Namespace patterns are recommended, not exclusive.
def is_allowed_extension_key(key: str) -> bool:
    """Return True for JSON-safe extension object keys."""
    if key in FINGERPRINT_EXTENSION_NAMESPACES:
        return True
    if key in {"domain", "dataProduct", "tenant", "tags", "customProperties"}:
        return True
    if _X_PREFIX.match(key):
        return True
    if _VENDOR_KEY.match(key):
        return True
    return bool(key) and not any(ord(ch) < 32 for ch in key)


def _depth_of(value: Any, depth: int = 0) -> int:
    if isinstance(value, dict):
        if not value:
            return depth
        return max(_depth_of(v, depth + 1) for v in value.values())
    if isinstance(value, list):
        if not value:
            return depth
        return max(_depth_of(v, depth + 1) for v in value)
    return depth


def _count_keys(value: Any) -> int:
    if isinstance(value, dict):
        return len(value) + sum(_count_keys(v) for v in value.values())
    if isinstance(value, list):
        return sum(_count_keys(v) for v in value)
    return 0


def validate_extensions(
    extensions: dict[str, Any],
    *,
    path: str = "extensions",
    max_bytes: int = DEFAULT_MAX_EXTENSION_BYTES,
    max_depth: int = DEFAULT_MAX_EXTENSION_DEPTH,
    max_keys: int = DEFAULT_MAX_EXTENSION_KEYS,
) -> None:
    """Validate extension keys and enforce size/depth/collection budgets."""
    for key in extensions:
        if not isinstance(key, str) or not is_allowed_extension_key(key):
            msg = f"Disallowed extension key at {path}: {key!r}"
            raise ExtensionBudgetError(msg)

    try:
        encoded = json.dumps(extensions, default=str, ensure_ascii=False).encode("utf-8")
    except (TypeError, ValueError) as exc:
        msg = f"Extensions at {path} are not JSON-serializable"
        raise ExtensionBudgetError(msg) from exc

    if len(encoded) > max_bytes:
        msg = f"Extensions at {path} exceed max_bytes={max_bytes} ({len(encoded)} bytes)"
        raise ExtensionBudgetError(msg)

    depth = _depth_of(extensions)
    if depth > max_depth:
        msg = f"Extensions at {path} exceed max_depth={max_depth} (depth={depth})"
        raise ExtensionBudgetError(msg)

    keys = _count_keys(extensions)
    if keys > max_keys:
        msg = f"Extensions at {path} exceed max_keys={max_keys} (keys={keys})"
        raise ExtensionBudgetError(msg)


def fingerprint_extensions(extensions: dict[str, Any]) -> dict[str, Any]:
    """Return the subset of extensions that participate in fingerprints."""
    return {k: v for k, v in extensions.items() if k in FINGERPRINT_EXTENSION_NAMESPACES}
