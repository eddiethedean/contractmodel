"""Canonical Contract Model (CCM) Pydantic models."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from contractmodel.core.constraints import FieldConstraints, SchemaConstraint
from contractmodel.core.types import ContractKind, ContractStatus, LogicalType


class Contact(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str | None = None
    name: str | None = None
    role: str | None = None


class Ownership(BaseModel):
    model_config = ConfigDict(extra="forbid")

    owner: str | None = None
    team: str | None = None
    contacts: list[Contact] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class SemanticMapping(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ontology_class: str | None = None
    ontology_property: str | None = None
    iri: str | None = None
    same_as: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class SemanticSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    namespaces: dict[str, str] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class QualityRule(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    type: str
    expression: str | None = None
    threshold: Any | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class QualitySpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rules: list[QualityRule] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ServiceLevelSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    freshness: str | None = None
    availability: str | None = None
    latency: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class LineageSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    upstream: list[str] = Field(default_factory=list)
    downstream: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class GovernanceSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    classification: str | None = None
    tags: list[str] = Field(default_factory=list)
    policies: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class IndexSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    fields: list[str] = Field(default_factory=list)
    unique: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class ContractField(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    logical_type: LogicalType
    required: bool = True
    nullable: bool = False

    description: str | None = None
    aliases: list[str] = Field(default_factory=list)

    default: Any | None = None
    examples: list[Any] = Field(default_factory=list)

    constraints: FieldConstraints = Field(default_factory=FieldConstraints)
    children: list[ContractField] = Field(default_factory=list)

    semantic: SemanticMapping | None = None

    metadata: dict[str, Any] = Field(default_factory=dict)
    extensions: dict[str, Any] = Field(default_factory=dict)


class ContractSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fields: list[ContractField]
    primary_key: list[str] = Field(default_factory=list)
    indexes: list[IndexSpec] = Field(default_factory=list)
    constraints: list[SchemaConstraint] = Field(default_factory=list)


class CanonicalContract(BaseModel):
    model_config = ConfigDict(extra="forbid")

    contract_id: str
    name: str
    version: str
    kind: ContractKind = ContractKind.DATASET
    description: str | None = None
    status: ContractStatus = ContractStatus.DRAFT

    ownership: Ownership | None = None
    schema: ContractSchema  # type: ignore[assignment]
    quality: QualitySpec | None = None
    service_level: ServiceLevelSpec | None = None
    lineage: LineageSpec | None = None
    semantics: SemanticSpec | None = None
    governance: GovernanceSpec | None = None

    metadata: dict[str, Any] = Field(default_factory=dict)
    extensions: dict[str, Any] = Field(default_factory=dict)


ContractField.model_rebuild()
