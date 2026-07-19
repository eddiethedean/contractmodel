"""Base model for generated contract Pydantic classes."""

from __future__ import annotations

from typing import ClassVar

from pydantic import BaseModel, ConfigDict

from contractmodel.versions import CCM_WIRE_VERSION


class ContractModel(BaseModel):
    """Base class for Pydantic models generated from contracts."""

    model_config = ConfigDict(extra="forbid")

    __contract_id__: ClassVar[str | None] = None
    __contract_version__: ClassVar[str | None] = None
    __contract_name__: ClassVar[str | None] = None
    __contract_fingerprint__: ClassVar[str | None] = None
    __ccm_wire_version__: ClassVar[str | None] = CCM_WIRE_VERSION
    __contract_kind__: ClassVar[str | None] = None
    __source_format__: ClassVar[str | None] = None
    __source_version__: ClassVar[str | None] = None


def attach_contract_identity(
    model: type[ContractModel],
    *,
    contract_id: str,
    version: str,
    name: str,
    fingerprint: str,
    kind: str | None = None,
    source_format: str | None = None,
    source_version: str | None = None,
    ccm_wire_version: str = CCM_WIRE_VERSION,
) -> type[ContractModel]:
    """Attach published contract identity metadata to a generated model class."""
    model.__contract_id__ = contract_id
    model.__contract_version__ = version
    model.__contract_name__ = name
    model.__contract_fingerprint__ = fingerprint
    model.__ccm_wire_version__ = ccm_wire_version
    model.__contract_kind__ = kind
    model.__source_format__ = source_format
    model.__source_version__ = source_version
    return model
