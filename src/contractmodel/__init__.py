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
from contractmodel.descriptor import describe_contract
from contractmodel.descriptor.models import (
    ConstraintDescriptor,
    ContractDescriptor,
    ContractFidelity,
    ContractIdentity,
    ContractProvenance,
    FidelityFinding,
    FidelityStatus,
    FieldDescriptor,
    IndexDescriptor,
    SchemaConstraintDescriptor,
    SchemaDescriptor,
)
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
    OdcsValidationError,
    OptionalDependencyError,
    RegistryError,
)
from contractmodel.export.registry import ExportStability, export_stability, known_export_targets
from contractmodel.extensions import ExtensionBudgetError
from contractmodel.fingerprint import canonical_bytes, fingerprint_contract
from contractmodel.model import ContractModel
from contractmodel.policy import DEFAULT_LOADING_POLICY, LoadingPolicy, LoadingPolicyError
from contractmodel.recognition import is_contract_model, resolve_contract_model
from contractmodel.versions import (
    CCM_WIRE_SCHEMA_ID,
    CCM_WIRE_VERSION,
    DEFAULT_ODCS_API_VERSION,
    SUPPORTED_ODCS_VERSIONS,
    SUPPORTED_PYDANTIC,
)
from contractmodel.wire import (
    canonical_ccm_dict,
    ccm_json_schema_text,
    export_ccm_json_schema,
    load_ccm_json_schema,
)

__all__ = [
    "BreakingChange",
    "CCM_WIRE_SCHEMA_ID",
    "CCM_WIRE_VERSION",
    "DEFAULT_LOADING_POLICY",
    "DEFAULT_ODCS_API_VERSION",
    "CanonicalContract",
    "ChangeType",
    "CompatibilityMode",
    "ConstraintDescriptor",
    "ContractDescriptor",
    "ContractDiff",
    "ContractFidelity",
    "ContractField",
    "ContractIdentity",
    "ContractModel",
    "ContractModelError",
    "ContractPluginError",
    "ContractProvenance",
    "ContractSchema",
    "DataContract",
    "ExportStability",
    "ExtensionBudgetError",
    "FieldChange",
    "FieldDescriptor",
    "FidelityFinding",
    "FidelityStatus",
    "IndexDescriptor",
    "LoadingPolicy",
    "LoadingPolicyError",
    "LogicalType",
    "NonBreakingChange",
    "OdcsImportError",
    "OdcsValidationError",
    "OptionalDependencyError",
    "RegistryError",
    "SUPPORTED_ODCS_VERSIONS",
    "SUPPORTED_PYDANTIC",
    "SchemaConstraintDescriptor",
    "SchemaDescriptor",
    "ValidationErrorDetail",
    "ValidationMode",
    "ValidationResult",
    "ValidationWarningDetail",
    "canonical_bytes",
    "canonical_ccm_dict",
    "ccm_json_schema_text",
    "describe_contract",
    "examples",
    "export_ccm_json_schema",
    "export_stability",
    "fingerprint_contract",
    "is_contract_model",
    "known_export_targets",
    "load_ccm_json_schema",
    "resolve_contract_model",
    "__version__",
]

__version__ = "0.2.0"
