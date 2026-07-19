"""Immutable contract descriptors for integrator introspection."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from contractmodel.core.types import LogicalType
from contractmodel.versions import CCM_WIRE_VERSION


class FidelityStatus(str, Enum):
    EXACT = "exact"
    NORMALIZED = "normalized"
    EXTENDED = "extended"
    LOSSY = "lossy"
    UNSUPPORTED = "unsupported"
    REJECTED = "rejected"


class FidelityFinding(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    code: str
    message: str
    path: str | None = None
    status: FidelityStatus = FidelityStatus.LOSSY


class ContractFidelity(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    status: FidelityStatus = FidelityStatus.EXACT
    findings: tuple[FidelityFinding, ...] = ()


class ContractIdentity(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    contract_id: str
    name: str
    version: str
    kind: str


class ContractProvenance(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    source_format: str | None = None
    source_version: str | None = None
    ccm_wire_version: str = CCM_WIRE_VERSION


class ConstraintDescriptor(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    min_value: Any | None = None
    max_value: Any | None = None
    min_length: int | None = None
    max_length: int | None = None
    pattern: str | None = None
    enum_values: tuple[Any, ...] | None = None
    unique: bool = False
    immutable: bool = False
    allowed_values: tuple[Any, ...] | None = None
    disallowed_values: tuple[Any, ...] | None = None


class FieldDescriptor(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    logical_type: LogicalType
    required: bool = True
    nullable: bool = False
    description: str | None = None
    aliases: tuple[str, ...] = ()
    default: Any | None = None
    examples: tuple[Any, ...] = ()
    constraints: ConstraintDescriptor = Field(default_factory=ConstraintDescriptor)
    children: tuple[FieldDescriptor, ...] = ()


class IndexDescriptor(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    fields: tuple[str, ...] = ()
    unique: bool = False


class SchemaConstraintDescriptor(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    type: str | None = None
    expression: str | None = None
    fields: tuple[str, ...] = ()


class SchemaDescriptor(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    fields: tuple[FieldDescriptor, ...]
    primary_key: tuple[str, ...] = ()
    indexes: tuple[IndexDescriptor, ...] = ()
    constraints: tuple[SchemaConstraintDescriptor, ...] = ()


class ContractDescriptor(BaseModel):
    """Deeply immutable, versioned contract introspection value."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    identity: ContractIdentity
    version: str
    schema_view: SchemaDescriptor
    fingerprint: str
    provenance: ContractProvenance
    fidelity: ContractFidelity
    ccm_wire_version: str = CCM_WIRE_VERSION
