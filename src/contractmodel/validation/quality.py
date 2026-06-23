"""Quality rule validation."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from contractmodel.core.ccm import CanonicalContract
from contractmodel.core.result import (
    ValidationErrorDetail,
    ValidationResult,
    ValidationWarningDetail,
)


def validate_quality_rules(
    contract: CanonicalContract,
    records: list[Mapping[str, Any]],
) -> ValidationResult:
    """Validate quality rules from the contract against records."""
    errors: list[ValidationErrorDetail] = []
    warnings: list[ValidationWarningDetail] = []

    if contract.quality is None:
        return ValidationResult(success=True, errors=[], warnings=[])

    for rule in contract.quality.rules:
        if rule.type == "completeness":
            for index, record in enumerate(records):
                for field in contract.contract_schema.fields:
                    if field.required and record.get(field.name) is None:
                        errors.append(
                            ValidationErrorDetail(
                                code="CM_QUALITY_COMPLETENESS",
                                message=(
                                    f"Completeness rule '{rule.name}' failed for '{field.name}'"
                                ),
                                field=field.name,
                                row=index,
                            )
                        )
        elif rule.type == "freshness":
            warnings.append(
                ValidationWarningDetail(
                    code="CM_QUALITY_FRESHNESS",
                    message=f"Freshness rule '{rule.name}' requires external evaluation",
                )
            )

    success = len(errors) == 0
    return ValidationResult(
        success=success,
        error_count=len(errors),
        warning_count=len(warnings),
        errors=errors,
        warnings=warnings,
        metrics={"records_total": len(records)},
    )
