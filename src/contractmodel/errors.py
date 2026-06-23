"""ContractModel errors."""

from __future__ import annotations


class ContractModelError(Exception):
    """Base error for ContractModel."""


class OptionalDependencyError(ContractModelError):
    """Raised when an optional extra is required but not installed."""

    def __init__(self, extra: str) -> None:
        message = (
            "Optional dependency not installed. "
            f"Install with: pip install contractmodel[{extra}]"
        )
        super().__init__(message)
        self.extra = extra


class OdcsImportError(ContractModelError):
    """Raised when an ODCS document cannot be imported."""


class ContractPluginError(ContractModelError):
    """Raised when a plugin fails."""


class RegistryError(ContractModelError):
    """Raised when registry operations fail."""
