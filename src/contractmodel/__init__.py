"""ContractModel — Python-native data contracts."""

from contractmodel.contract import DataContract
from contractmodel.core.ccm import CanonicalContract, ContractField, ContractSchema
from contractmodel.core.result import ValidationErrorDetail, ValidationResult
from contractmodel.diff.engine import BreakingChange, ContractDiff, FieldChange, NonBreakingChange
from contractmodel.model import ContractModel

__all__ = [
    "BreakingChange",
    "CanonicalContract",
    "ContractDiff",
    "ContractField",
    "ContractModel",
    "ContractSchema",
    "DataContract",
    "FieldChange",
    "NonBreakingChange",
    "ValidationErrorDetail",
    "ValidationResult",
]

__version__ = "0.1.1"
