"""Tests for SARIF output."""

from contractmodel.core.result import ValidationErrorDetail, ValidationResult
from contractmodel.validation.sarif import validation_result_to_sarif


def test_validation_result_to_sarif() -> None:
    result = ValidationResult(
        success=False,
        error_count=1,
        errors=[
            ValidationErrorDetail(
                code="CM_SCHEMA_MISSING_FIELD",
                message="Missing field",
                field="id",
                row=0,
            )
        ],
    )
    sarif = validation_result_to_sarif(result)
    assert sarif["version"] == "2.1.0"
    assert sarif["runs"][0]["results"][0]["ruleId"] == "CM_SCHEMA_MISSING_FIELD"


def test_validation_result_to_sarif_maps_location_and_rules() -> None:
    result = ValidationResult(
        success=False,
        error_count=3,
        errors=[
            ValidationErrorDetail(
                code="CM_SCHEMA_MISSING_FIELD",
                message="Missing",
                field="id",
                row=2,
            ),
            ValidationErrorDetail(
                code="CM_SCHEMA_MISSING_FIELD",
                message="Also missing",
                field="name",
                row=3,
            ),
            ValidationErrorDetail(
                code="CM_RUNTIME_ERROR",
                message="Bad JSON",
                field=None,
            ),
        ],
    )
    sarif = validation_result_to_sarif(result, tool_name="my-tool")
    assert sarif["runs"][0]["tool"]["driver"]["name"] == "my-tool"
    assert len(sarif["runs"][0]["tool"]["driver"]["rules"]) == 2
    region = sarif["runs"][0]["results"][0]["locations"][0]["physicalLocation"]["region"]
    assert region["startLine"] == 3
    assert sarif["runs"][0]["results"][-1]["locations"] == []
