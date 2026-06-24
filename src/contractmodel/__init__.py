"""ContractModel — Python-native data contracts."""

from contractmodel.contract import DataContract
from contractmodel.core.ccm import CanonicalContract, ContractField, ContractSchema
from contractmodel.core.result import (
    ValidationErrorDetail,
    ValidationResult,
    ValidationWarningDetail,
)
from contractmodel.core.types import CompatibilityMode, ValidationMode
from contractmodel.diff.engine import BreakingChange, ContractDiff, FieldChange, NonBreakingChange
from contractmodel.model import ContractModel

__all__ = [
    "BreakingChange",
    "CanonicalContract",
    "CompatibilityMode",
    "ContractDiff",
    "ContractField",
    "ContractModel",
    "ContractSchema",
    "DataContract",
    "FieldChange",
    "NonBreakingChange",
    "ValidationErrorDetail",
    "ValidationMode",
    "ValidationResult",
    "ValidationWarningDetail",
    "__version__",
]

__version__ = "0.1.2"
