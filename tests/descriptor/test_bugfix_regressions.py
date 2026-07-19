"""Regression tests for 0.2.0 deep-dive bug fixes."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pytest

from contractmodel import (
    CanonicalContract,
    ContractField,
    ContractSchema,
    DataContract,
    ExtensionBudgetError,
    LoadingPolicy,
    LoadingPolicyError,
    LogicalType,
    describe_contract,
    fingerprint_contract,
)
from contractmodel.core.ccm import IndexSpec
from contractmodel.core.constraints import FieldConstraints, SchemaConstraint
from contractmodel.core.types import ContractKind


def test_descriptor_indexes_are_deeply_immutable() -> None:
    ccm = CanonicalContract(
        contract_id="idx",
        name="Idx",
        version="1.0.0",
        schema=ContractSchema(
            fields=[ContractField(name="id", logical_type=LogicalType.STRING)],
            indexes=[IndexSpec(name="pk", fields=["id"], unique=True)],
            constraints=[SchemaConstraint(name="ck", fields=["id"])],
        ),
    )
    descriptor = describe_contract(ccm)
    with pytest.raises((TypeError, AttributeError, ValueError)):
        descriptor.schema_view.indexes[0].name = "MUTATED"  # type: ignore[misc]
    assert descriptor.schema_view.indexes[0].name == "pk"
    assert descriptor.schema_view.constraints[0].name == "ck"


def test_nested_field_extensions_are_budgeted() -> None:
    huge = "y" * 70_000
    data = {
        "contract_id": "n",
        "name": "N",
        "version": "1.0.0",
        "schema": {
            "fields": [
                {
                    "name": "parent",
                    "logical_type": "object",
                    "children": [
                        {
                            "name": "child",
                            "logical_type": "string",
                            "extensions": {"x-huge": huge},
                        }
                    ],
                }
            ]
        },
    }
    # Raise collection/byte gates so the nested extension budget is what fires.
    policy = LoadingPolicy(max_bytes=None, max_collection_size=None)
    with pytest.raises(ExtensionBudgetError, match="max_bytes"):
        DataContract.from_dict(data, policy=policy)


def test_from_dict_honors_max_bytes() -> None:
    data = {
        "contract_id": "b",
        "name": "B",
        "version": "1.0.0",
        "description": "x" * 5_000,
        "schema": {"fields": [{"name": "id", "logical_type": "string"}]},
    }
    with pytest.raises(LoadingPolicyError, match="max_bytes"):
        DataContract.from_dict(data, policy=LoadingPolicy(max_bytes=100))


def test_require_odcs_version_does_not_break_ccm() -> None:
    data = {
        "contract_id": "c",
        "name": "C",
        "version": "1.0.0",
        "schema": {"fields": [{"name": "id", "logical_type": "string"}]},
    }
    contract = DataContract.from_dict(data, policy=LoadingPolicy(require_odcs_version=True))
    assert contract.source_format == "ccm"


def test_intermediate_directory_symlink_blocked(tmp_path: Path) -> None:
    real_dir = tmp_path / "real"
    real_dir.mkdir()
    contract_path = real_dir / "c.yaml"
    contract_path.write_text(
        "contract_id: x\nname: X\nversion: 1.0.0\nschema:\n  fields: []\n",
        encoding="utf-8",
    )
    link_dir = tmp_path / "link"
    try:
        link_dir.symlink_to(real_dir)
    except OSError:
        pytest.skip("symlinks unavailable")
    with pytest.raises(LoadingPolicyError, match="Symlink"):
        DataContract.load(
            link_dir / "c.yaml",
            policy=LoadingPolicy(follow_symlinks=False, approved_roots=(tmp_path,)),
        )


def test_odcs_provenance_without_api_version() -> None:
    data = {
        "kind": "DataContract",
        "id": "legacy",
        "name": "Legacy",
        "version": "1.0.0",
        "schema": [{"name": "id", "logicalType": "string"}],
    }
    contract = DataContract.from_odcs_dict(data)
    assert contract.source_format == "odcs"
    assert describe_contract(contract).provenance.source_format == "odcs"


def test_ccm_with_apiVersion_extension_stays_ccm() -> None:
    data = {
        "contract_id": "c",
        "name": "C",
        "version": "1.0.0",
        "extensions": {"apiVersion": "v3.1.0"},
        "schema": {"fields": [{"name": "id", "logical_type": "string"}]},
    }
    contract = DataContract.from_dict(data)
    assert contract.source_format == "ccm"
    assert describe_contract(contract).provenance.source_format == "ccm"


def test_fingerprint_unifies_numeric_forms_and_rejects_nan_decimal() -> None:
    def make(min_value: object) -> CanonicalContract:
        return CanonicalContract(
            contract_id="n",
            name="N",
            version="1.0.0",
            kind=ContractKind.TABLE,
            schema=ContractSchema(
                fields=[
                    ContractField(
                        name="amount",
                        logical_type=LogicalType.NUMBER,
                        constraints=FieldConstraints(min_value=min_value),  # type: ignore[arg-type]
                    )
                ]
            ),
        )

    assert fingerprint_contract(make(1)) == fingerprint_contract(make(1.0))
    assert fingerprint_contract(make(1)) == fingerprint_contract(make(Decimal("1.0")))
    with pytest.raises(ValueError, match="Non-finite"):
        fingerprint_contract(make(Decimal("NaN")))


def test_describe_contract_model_instance() -> None:
    contract = DataContract.from_ccm(
        CanonicalContract(
            contract_id="inst",
            name="Inst",
            version="1.0.0",
            schema=ContractSchema(
                fields=[ContractField(name="id", logical_type=LogicalType.STRING)]
            ),
        )
    )
    model = contract.to_pydantic()
    instance = model(id="x")
    described = describe_contract(instance)
    assert described.identity.contract_id == "inst"


def test_loading_policy_frozenset_json_is_sorted() -> None:
    policy = LoadingPolicy(
        allowed_formats=frozenset({"odcs", "ccm"}),
        allowed_encodings=frozenset({"json", "yaml"}),
        allowed_odcs_versions=frozenset({"v3.1.0", "v3.0.0"}),
    )
    dumped = policy.model_dump(mode="json")
    assert dumped["allowed_formats"] == ["ccm", "odcs"]
    assert dumped["allowed_encodings"] == ["json", "yaml"]
    assert dumped["allowed_odcs_versions"] == ["v3.0.0", "v3.1.0"]


def test_allowed_formats_mean_content_formats(tmp_path: Path) -> None:
    path = tmp_path / "c.yaml"
    path.write_text(
        "contract_id: x\nname: X\nversion: 1.0.0\nschema:\n  fields: []\n",
        encoding="utf-8",
    )
    # yaml encoding allowed; content is ccm — should succeed
    DataContract.load(path, policy=LoadingPolicy(approved_roots=(tmp_path,)))
    with pytest.raises(LoadingPolicyError, match="encoding"):
        DataContract.load(
            path,
            policy=LoadingPolicy(
                approved_roots=(tmp_path,),
                allowed_encodings=frozenset({"json"}),
            ),
        )
