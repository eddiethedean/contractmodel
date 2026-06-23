"""SARIF output formatting."""

from __future__ import annotations

from typing import Any

from contractmodel.core.result import ValidationResult


def validation_result_to_sarif(
    result: ValidationResult,
    *,
    tool_name: str = "contractmodel",
) -> dict[str, Any]:
    """Convert a ValidationResult to SARIF 2.1.0."""
    rules = []
    results = []
    rule_ids: set[str] = set()

    for error in result.errors:
        if error.code not in rule_ids:
            rule_ids.add(error.code)
            rules.append(
                {
                    "id": error.code,
                    "shortDescription": {"text": error.code},
                }
            )
        location: dict[str, Any] = {}
        if error.field:
            location = {
                "physicalLocation": {
                    "artifactLocation": {"uri": "data"},
                    "region": {"startLine": (error.row or 0) + 1},
                }
            }
        results.append(
            {
                "ruleId": error.code,
                "message": {"text": error.message},
                "level": "error",
                "locations": [location] if location else [],
            }
        )

    return {
        "version": "2.1.0",
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": tool_name,
                        "rules": rules,
                    }
                },
                "results": results,
            }
        ],
    }
