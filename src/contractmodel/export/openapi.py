"""OpenAPI export."""

from __future__ import annotations

from typing import Any

from contractmodel.core.ccm import CanonicalContract
from contractmodel.export.json_schema import export_json_schema


def export_openapi(contract: CanonicalContract) -> dict[str, Any]:
    """Export a contract as a minimal OpenAPI 3.1 document."""
    schema_name = contract.name.replace(" ", "")
    schema = export_json_schema(contract)
    return {
        "openapi": "3.1.0",
        "info": {
            "title": contract.name,
            "version": contract.version,
            "description": contract.description or "",
        },
        "components": {
            "schemas": {
                schema_name: schema,
            }
        },
    }
