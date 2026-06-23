"""Plugin protocols."""

from __future__ import annotations

from typing import Any, Protocol

from contractmodel.core.ccm import CanonicalContract
from contractmodel.core.result import ValidationResult


class ValidatorPlugin(Protocol):
    name: str
    version: str

    def validate(self, contract: CanonicalContract, data: Any) -> ValidationResult: ...


class ExporterPlugin(Protocol):
    name: str
    version: str
    target: str

    def export(self, contract: CanonicalContract) -> str | bytes | dict[str, Any]: ...


class RegistryPlugin(Protocol):
    name: str
    version: str

    def publish(self, contract: CanonicalContract) -> Any: ...
    def fetch(self, contract_id: str, version: str | None = None) -> CanonicalContract: ...


class SemanticPlugin(Protocol):
    name: str
    version: str

    def export_rdf(self, contract: CanonicalContract) -> str: ...
    def export_shacl(self, contract: CanonicalContract) -> str: ...
    def export_owl(self, contract: CanonicalContract) -> str: ...
