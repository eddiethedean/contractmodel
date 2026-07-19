"""Build frozen contract descriptors from CCM and related sources."""

from __future__ import annotations

from typing import Any

from contractmodel.core.ccm import CanonicalContract, ContractField
from contractmodel.core.constraints import FieldConstraints
from contractmodel.core.result import ValidationWarningDetail
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
from contractmodel.fingerprint import fingerprint_contract
from contractmodel.model import ContractModel
from contractmodel.versions import CCM_WIRE_VERSION


def _tuple_or_none(values: list[Any] | None) -> tuple[Any, ...] | None:
    if values is None:
        return None
    return tuple(values)


def _constraint_descriptor(constraints: FieldConstraints) -> ConstraintDescriptor:
    return ConstraintDescriptor(
        min_value=constraints.min_value,
        max_value=constraints.max_value,
        min_length=constraints.min_length,
        max_length=constraints.max_length,
        pattern=constraints.pattern,
        enum_values=_tuple_or_none(constraints.enum_values),
        unique=constraints.unique,
        immutable=constraints.immutable,
        allowed_values=_tuple_or_none(constraints.allowed_values),
        disallowed_values=_tuple_or_none(constraints.disallowed_values),
    )


def _field_descriptor(field: ContractField) -> FieldDescriptor:
    return FieldDescriptor(
        name=field.name,
        logical_type=field.logical_type,
        required=field.required,
        nullable=field.nullable,
        description=field.description,
        aliases=tuple(field.aliases),
        default=field.default,
        examples=tuple(field.examples),
        constraints=_constraint_descriptor(field.constraints),
        children=tuple(_field_descriptor(child) for child in field.children),
    )


def _fidelity_from_warnings(
    warnings: list[ValidationWarningDetail] | None,
    *,
    inferred: bool = False,
) -> ContractFidelity:
    findings: list[FidelityFinding] = []
    status = FidelityStatus.EXACT
    if inferred:
        status = FidelityStatus.NORMALIZED
        findings.append(
            FidelityFinding(
                code="IDENTITY_INFERRED",
                message="Contract identity was inferred from a plain Pydantic model",
                status=FidelityStatus.NORMALIZED,
            )
        )
    for warning in warnings or []:
        findings.append(
            FidelityFinding(
                code=warning.code,
                message=warning.message,
                path=warning.field,
                status=FidelityStatus.LOSSY,
            )
        )
        status = FidelityStatus.LOSSY
    return ContractFidelity(status=status, findings=tuple(findings))


def describe_canonical(
    contract: CanonicalContract,
    *,
    source_format: str | None = None,
    source_version: str | None = None,
    import_warnings: list[ValidationWarningDetail] | None = None,
    inferred: bool = False,
) -> ContractDescriptor:
    """Build an immutable descriptor from a CanonicalContract snapshot."""
    snapshot = contract.model_copy(deep=True)
    schema = SchemaDescriptor(
        fields=tuple(_field_descriptor(field) for field in snapshot.contract_schema.fields),
        primary_key=tuple(snapshot.contract_schema.primary_key),
        indexes=tuple(
            IndexDescriptor(
                name=index.name,
                fields=tuple(index.fields),
                unique=index.unique,
            )
            for index in snapshot.contract_schema.indexes
        ),
        constraints=tuple(
            SchemaConstraintDescriptor(
                name=item.name,
                type=item.type,
                expression=item.expression,
                fields=tuple(item.fields),
            )
            for item in snapshot.contract_schema.constraints
        ),
    )
    identity = ContractIdentity(
        contract_id=snapshot.contract_id,
        name=snapshot.name,
        version=snapshot.version,
        kind=snapshot.kind.value,
    )
    provenance = ContractProvenance(
        source_format=source_format,
        source_version=source_version
        or (
            str(snapshot.extensions.get("apiVersion"))
            if snapshot.extensions.get("apiVersion") is not None
            else None
        ),
        ccm_wire_version=CCM_WIRE_VERSION,
    )
    return ContractDescriptor(
        identity=identity,
        version=snapshot.version,
        schema_view=schema,
        fingerprint=fingerprint_contract(snapshot),
        provenance=provenance,
        fidelity=_fidelity_from_warnings(import_warnings, inferred=inferred),
        ccm_wire_version=CCM_WIRE_VERSION,
    )


def describe_contract(source: Any) -> ContractDescriptor:
    """Describe a DataContract, CanonicalContract, or ContractModel class/instance."""
    from contractmodel.contract import DataContract

    if isinstance(source, DataContract):
        source_format = getattr(source, "source_format", None) or "ccm"
        source_version = None
        if source_format == "odcs":
            api_version = source.ccm.extensions.get("apiVersion")
            source_version = str(api_version) if api_version is not None else None
        return describe_canonical(
            source.ccm,
            source_format=source_format,
            source_version=source_version,
            import_warnings=list(source.import_warnings),
        )

    if isinstance(source, CanonicalContract):
        return describe_canonical(source, source_format="ccm")

    if isinstance(source, ContractModel):
        return describe_contract(type(source))

    if isinstance(source, type) and issubclass(source, ContractModel):
        from contractmodel.adapters.pydantic import contract_from_pydantic

        contract = contract_from_pydantic(source)
        inferred = getattr(source, "__contract_id__", None) is None
        source_format = getattr(source, "__source_format__", None) or "pydantic"
        source_version = getattr(source, "__source_version__", None)
        return describe_canonical(
            contract,
            source_format=source_format,
            source_version=str(source_version) if source_version is not None else None,
            inferred=inferred,
        )

    msg = f"Unsupported describe_contract source: {type(source)!r}"
    raise TypeError(msg)
