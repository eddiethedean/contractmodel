"""ODCS export wrapper."""

from __future__ import annotations

from typing import Any

from contractmodel.adapters.odcs import export_odcs as _export_odcs
from contractmodel.core.ccm import CanonicalContract


def export_odcs(contract: CanonicalContract) -> dict[str, Any]:
    """Export a CanonicalContract to ODCS."""
    return _export_odcs(contract)
