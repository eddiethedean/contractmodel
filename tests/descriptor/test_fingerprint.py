"""Fingerprint stability tests."""

from __future__ import annotations

from contractmodel import CanonicalContract, ContractField, ContractSchema, LogicalType
from contractmodel.core.constraints import FieldConstraints
from contractmodel.fingerprint import canonical_bytes, fingerprint_contract


def _contract(*, description: str | None = "hello") -> CanonicalContract:
    return CanonicalContract(
        contract_id="orders",
        name="Orders",
        version="2.0.0",
        description=description,
        schema=ContractSchema(
            fields=[
                ContractField(
                    name="b",
                    logical_type=LogicalType.INTEGER,
                    description="second",
                    constraints=FieldConstraints(min_value=0),
                ),
                ContractField(
                    name="a",
                    logical_type=LogicalType.STRING,
                    nullable=True,
                    required=False,
                ),
            ]
        ),
        extensions={"apiVersion": "v3.1.0", "x-custom": "nope"},
    )


def test_fingerprint_stable_across_equivalent_construction() -> None:
    left = _contract()
    right = CanonicalContract(
        contract_id="orders",
        name="Orders",
        version="2.0.0",
        description="different description",
        schema=ContractSchema(
            fields=[
                ContractField(
                    name="b",
                    logical_type=LogicalType.INTEGER,
                    description="ignored",
                    constraints=FieldConstraints(min_value=0),
                ),
                ContractField(
                    name="a",
                    logical_type=LogicalType.STRING,
                    nullable=True,
                    required=False,
                ),
            ]
        ),
        extensions={"apiVersion": "v3.1.0", "x-custom": "changed"},
    )
    assert fingerprint_contract(left) == fingerprint_contract(right)
    assert canonical_bytes(left) == canonical_bytes(right)


def test_fingerprint_changes_when_nullability_changes() -> None:
    base = _contract()
    changed = base.model_copy(deep=True)
    changed.contract_schema.fields[1].nullable = False
    assert fingerprint_contract(base) != fingerprint_contract(changed)


def test_fingerprint_includes_nested_children() -> None:
    flat = _contract()
    nested = flat.model_copy(deep=True)
    nested.contract_schema.fields[0].children = [
        ContractField(name="nested", logical_type=LogicalType.STRING)
    ]
    assert fingerprint_contract(flat) != fingerprint_contract(nested)
