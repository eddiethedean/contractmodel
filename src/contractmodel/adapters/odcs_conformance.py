"""ODCS document conformance via pyodcs."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pyodcs

from contractmodel.errors import OdcsValidationError

_ERROR_SEVERITY = "error"


def _error_diagnostics(report: dict[str, Any]) -> list[dict[str, Any]]:
    diagnostics = report.get("diagnostics")
    if not isinstance(diagnostics, list):
        return []
    return [
        diagnostic
        for diagnostic in diagnostics
        if isinstance(diagnostic, dict)
        and diagnostic.get("severity", _ERROR_SEVERITY) == _ERROR_SEVERITY
    ]


def _raise_if_invalid(report: dict[str, Any], *, context: str) -> None:
    errors = _error_diagnostics(report)
    if not errors and pyodcs.is_valid(report):
        return
    if not errors:
        errors = list(report.get("diagnostics") or [])
    codes = ", ".join(
        str(diagnostic.get("id", "odcs:unknown"))
        for diagnostic in errors[:5]
        if isinstance(diagnostic, dict)
    )
    message = f"ODCS document failed conformance ({context})"
    if codes:
        message = f"{message}: {codes}"
    raise OdcsValidationError(message, diagnostics=errors)


def validate_odcs_document(data: dict[str, Any]) -> None:
    """Validate a parsed ODCS document dict with pyodcs (fail closed on errors)."""
    try:
        report = pyodcs.validate(data)
    except (TypeError, ValueError) as exc:
        raise OdcsValidationError(
            f"ODCS document failed conformance (validate): {exc}",
            diagnostics=[
                {
                    "id": "odcs:validate-error",
                    "severity": _ERROR_SEVERITY,
                    "message": str(exc),
                }
            ],
        ) from exc
    _raise_if_invalid(report, context="validate")


def parse_and_validate_odcs_file(path: str | Path) -> dict[str, Any]:
    """Parse and validate an ODCS file; return the contract dict."""
    result = pyodcs.parse_file(str(path))
    report = pyodcs.validate_result(result)
    _raise_if_invalid(report, context=f"parse_file:{path}")
    contract = result.get("contract")
    if not isinstance(contract, dict):
        raise OdcsValidationError(
            f"ODCS parse produced no contract ({path})",
            diagnostics=_error_diagnostics(report),
        )
    return contract


def parse_and_validate_odcs(
    content: str | bytes,
    *,
    format: str = "yaml",
) -> dict[str, Any]:
    """Parse and validate ODCS text; return the contract dict."""
    result = pyodcs.parse(content, format=format)
    report = pyodcs.validate_result(result)
    _raise_if_invalid(report, context=f"parse:{format}")
    contract = result.get("contract")
    if not isinstance(contract, dict):
        raise OdcsValidationError(
            "ODCS parse produced no contract",
            diagnostics=_error_diagnostics(report),
        )
    return contract


def diff_odcs_documents(old: dict[str, Any], new: dict[str, Any]) -> dict[str, Any]:
    """Compare two ODCS document dicts using pyodcs compatibility analysis."""
    validate_odcs_document(old)
    validate_odcs_document(new)
    report = pyodcs.diff(old, new)
    if not isinstance(report, dict):
        msg = "pyodcs.diff returned a non-dict report"
        raise OdcsValidationError(msg)
    return report
