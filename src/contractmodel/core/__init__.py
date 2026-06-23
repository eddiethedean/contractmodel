"""ContractModel core package."""

from contractmodel.core.ccm import (
    CanonicalContract,
    Contact,
    ContractField,
    ContractSchema,
    GovernanceSpec,
    IndexSpec,
    LineageSpec,
    Ownership,
    QualityRule,
    QualitySpec,
    SemanticMapping,
    SemanticSpec,
    ServiceLevelSpec,
)
from contractmodel.core.constraints import CustomConstraint, FieldConstraints, SchemaConstraint
from contractmodel.core.result import (
    ValidationErrorDetail,
    ValidationResult,
    ValidationWarningDetail,
)
from contractmodel.core.types import (
    CompatibilityMode,
    ContractKind,
    ContractStatus,
    LogicalType,
    ValidationMode,
)

__all__ = [
    "CanonicalContract",
    "CompatibilityMode",
    "Contact",
    "ContractField",
    "ContractKind",
    "ContractSchema",
    "ContractStatus",
    "CustomConstraint",
    "FieldConstraints",
    "GovernanceSpec",
    "IndexSpec",
    "LineageSpec",
    "LogicalType",
    "Ownership",
    "QualityRule",
    "QualitySpec",
    "SchemaConstraint",
    "SemanticMapping",
    "SemanticSpec",
    "ServiceLevelSpec",
    "ValidationErrorDetail",
    "ValidationMode",
    "ValidationResult",
    "ValidationWarningDetail",
]
