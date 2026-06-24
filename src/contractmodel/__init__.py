"""ContractModel — Python-native data contracts."""

from contractmodel import examples as examples
from contractmodel.contract import DataContract
from contractmodel.core.ccm import CanonicalContract, ContractField, ContractSchema
from contractmodel.core.result import (
    ValidationErrorDetail,
    ValidationResult,
    ValidationWarningDetail,
)
from contractmodel.core.types import CompatibilityMode, LogicalType, ValidationMode
from contractmodel.diff.engine import (
    BreakingChange,
    ChangeType,
    ContractDiff,
    FieldChange,
    NonBreakingChange,
)
from contractmodel.errors import (
    ContractModelError,
    ContractPluginError,
    OdcsImportError,
    OptionalDependencyError,
    RegistryError,
)
from contractmodel.model import ContractModel

__all__ = [
    "BreakingChange",
    "CanonicalContract",
    "ChangeType",
    "CompatibilityMode",
    "ContractDiff",
    "ContractField",
    "ContractModel",
    "ContractModelError",
    "ContractPluginError",
    "ContractSchema",
    "DataContract",
    "FieldChange",
    "LogicalType",
    "NonBreakingChange",
    "OdcsImportError",
    "OptionalDependencyError",
    "RegistryError",
    "ValidationErrorDetail",
    "ValidationMode",
    "ValidationResult",
    "ValidationWarningDetail",
    "examples",
    "__version__",
]

__version__ = "0.1.2"
