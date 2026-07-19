"""Extra coverage for 0.2 kernel modules."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pytest
from pydantic import BaseModel

from contractmodel import (
    CanonicalContract,
    ContractField,
    ContractModel,
    ContractSchema,
    DataContract,
    LogicalType,
    OdcsImportError,
    describe_contract,
    export_stability,
    fingerprint_contract,
    known_export_targets,
    resolve_contract_model,
)
from contractmodel.descriptor.models import FidelityStatus
from contractmodel.extensions import (
    ExtensionBudgetError,
    is_allowed_extension_key,
    validate_extensions,
)
from contractmodel.fingerprint import canonical_bytes
from contractmodel.policy import (
    LoadingPolicy,
    LoadingPolicyError,
    enforce_document_bounds,
    resolve_contract_path,
)
from contractmodel.versions import is_supported_odcs_version, normalize_odcs_api_version
from contractmodel.wire import (
    canonical_ccm_dict,
    ccm_json_schema_text,
    export_ccm_json_schema,
)


def test_extension_key_rules_and_budgets() -> None:
    assert is_allowed_extension_key("x-foo")
    assert is_allowed_extension_key("vendor.meta")
    assert not is_allowed_extension_key("")
    assert not is_allowed_extension_key("bad\nkey")
    with pytest.raises(ExtensionBudgetError, match="max_depth"):
        validate_extensions({"x-a": {"b": {"c": 1}}}, max_depth=1)
    with pytest.raises(ExtensionBudgetError, match="max_keys"):
        validate_extensions({f"x-{i}": i for i in range(300)}, max_keys=50)
    cyclic: dict[str, object] = {}
    cyclic["x-loop"] = cyclic
    with pytest.raises(ExtensionBudgetError, match="JSON-serializable"):
        validate_extensions(cyclic)


def test_fingerprint_handles_decimal_and_enum_constraints() -> None:
    from contractmodel.core.constraints import FieldConstraints
    from contractmodel.core.types import ContractKind

    contract = CanonicalContract(
        contract_id="d",
        name="D",
        version="1.0.0",
        kind=ContractKind.TABLE,
        schema=ContractSchema(
            fields=[
                ContractField(
                    name="amount",
                    logical_type=LogicalType.DECIMAL,
                    constraints=FieldConstraints(min_value=Decimal("1.50"), enum_values=["a", "b"]),
                )
            ]
        ),
    )
    assert len(fingerprint_contract(contract)) == 64
    assert b"1.5" in canonical_bytes(contract)


def test_describe_contract_model_and_plain_basemodel() -> None:
    contract = DataContract.from_ccm(
        CanonicalContract(
            contract_id="m",
            name="M",
            version="9.9.9",
            schema=ContractSchema(
                fields=[ContractField(name="id", logical_type=LogicalType.STRING)]
            ),
        )
    )
    model = contract.to_pydantic()
    described = describe_contract(model)
    assert described.identity.contract_id == "m"
    assert described.identity.version == "9.9.9"

    class Plain(BaseModel):
        id: str

    inferred = describe_contract(DataContract.from_pydantic(Plain).to_pydantic())
    # generated from inferred CCM still has ClassVars after to_pydantic
    assert inferred.identity.contract_id

    with pytest.raises(TypeError):
        describe_contract(123)


def test_resolve_annotation_edges() -> None:
    from typing import Annotated

    assert resolve_contract_model(None) is None
    assert resolve_contract_model(Annotated[str, "x"]) is None
    assert resolve_contract_model(str | None) is None


def test_policy_symlink_and_version_gates(tmp_path: Path) -> None:
    target = tmp_path / "c.yaml"
    target.write_text(
        "contract_id: x\nname: X\nversion: 1.0.0\nschema:\n  fields: []\n",
        encoding="utf-8",
    )
    link = tmp_path / "link.yaml"
    try:
        link.symlink_to(target)
    except OSError:
        pytest.skip("symlinks unavailable")
    with pytest.raises(LoadingPolicyError, match="Symlink"):
        policy = LoadingPolicy(follow_symlinks=False, approved_roots=(tmp_path,))
        resolve_contract_path(link, policy)

    enforce_document_bounds({"id": "x"}, format_name="ccm")
    with pytest.raises(LoadingPolicyError, match="not allowed"):
        policy = LoadingPolicy(allowed_formats=frozenset({"odcs"}))
        enforce_document_bounds({}, policy, format_name="ccm")
    with pytest.raises(LoadingPolicyError, match="apiVersion"):
        enforce_document_bounds(
            {},
            LoadingPolicy(require_odcs_version=True),
            format_name="odcs",
            odcs_api_version=None,
        )


def test_versions_and_export_registry() -> None:
    assert normalize_odcs_api_version("  v3.1.0 ") == "v3.1.0"
    assert normalize_odcs_api_version("") is None
    assert is_supported_odcs_version(None) is False
    assert is_supported_odcs_version("v3.1.0")
    assert not is_supported_odcs_version("v0.0.1")
    assert "odcs" in known_export_targets()
    assert export_stability("unknown-format").value == "private"


def test_wire_helpers_and_nonfinite_rejection() -> None:
    text = ccm_json_schema_text()
    assert "contractmodel.ccm/1" in text
    schema = export_ccm_json_schema()
    assert schema["title"] == "contractmodel.ccm/1"
    contract = CanonicalContract(
        contract_id="w",
        name="W",
        version="1.0.0",
        schema=ContractSchema(fields=[ContractField(name="id", logical_type=LogicalType.STRING)]),
    )
    wire = canonical_ccm_dict(contract)
    assert wire["schema"]["fields"][0]["logical_type"] == "string"
    with pytest.raises(ValueError, match="Non-finite"):
        from contractmodel.wire import _jsonable

        _jsonable(float("nan"))


def test_odcs_nested_items_list_and_children_key() -> None:
    from contractmodel.adapters.odcs import import_odcs

    data = {
        "apiVersion": "v3.1.0",
        "kind": "DataContract",
        "id": "n",
        "name": "N",
        "version": "1.0.0",
        "status": "draft",
        "schema": [
            {
                "name": "payload",
                "logicalType": "object",
                "children": [{"name": "ok", "logicalType": "boolean"}],
            },
            {
                "name": "vals",
                "logicalType": "array",
                "items": [
                    {"name": "one", "logicalType": "integer"},
                ],
            },
        ],
    }
    # Mapping-only path: pyodcs rejects non-standard children/items shapes.
    contract = import_odcs(data)
    assert contract.contract_schema.fields[0].children[0].name == "ok"
    assert contract.contract_schema.fields[1].children[0].name == "item"


def test_fingerprint_rejects_nonfinite_and_bad_types() -> None:
    from contractmodel.fingerprint import _canon_value

    with pytest.raises(ValueError, match="Non-finite"):
        _canon_value(float("inf"))
    with pytest.raises(TypeError, match="Unsupported"):
        _canon_value(object())


def test_wire_rejects_bad_values() -> None:
    from contractmodel.wire import _jsonable

    with pytest.raises(ValueError, match="Non-finite"):
        _jsonable(float("inf"))
    with pytest.raises(TypeError, match="Unsupported"):
        _jsonable(object())
    assert _jsonable(Decimal("2")) == "2"
    assert _jsonable((1, 2)) == [1, 2]


def test_policy_depth_and_collection_limits() -> None:
    deep = {"a": {"b": {"c": {"d": 1}}}}
    with pytest.raises(LoadingPolicyError, match="max_depth"):
        enforce_document_bounds(deep, LoadingPolicy(max_depth=2))
    wide = {"fields": list(range(20))}
    with pytest.raises(LoadingPolicyError, match="max_collection_size"):
        enforce_document_bounds(wide, LoadingPolicy(max_collection_size=5))


def test_policy_missing_file(tmp_path: Path) -> None:
    missing = tmp_path / "nope.yaml"
    with pytest.raises(LoadingPolicyError, match="not a file"):
        resolve_contract_path(missing, LoadingPolicy(approved_roots=(tmp_path,)))


def test_extension_list_depth_and_disallowed_key() -> None:
    with pytest.raises(ExtensionBudgetError, match="Disallowed"):
        validate_extensions({"": 1})
    validate_extensions({"x-ok": []})
    validate_extensions({"domain": "sales"})


def test_recognition_annotated_contract_model() -> None:
    from typing import Annotated

    contract = DataContract.from_ccm(
        CanonicalContract(
            contract_id="ann",
            name="Ann",
            version="1.0.0",
            schema=ContractSchema(
                fields=[ContractField(name="id", logical_type=LogicalType.STRING)]
            ),
        )
    )
    model = contract.to_pydantic()
    assert resolve_contract_model(Annotated[model, "tag"]) is model


def test_odcs_invalid_status_and_type() -> None:
    from contractmodel.adapters.odcs import import_odcs

    with pytest.raises(OdcsImportError, match="status"):
        import_odcs(
            {
                "apiVersion": "v3.1.0",
                "kind": "DataContract",
                "id": "x",
                "name": "X",
                "version": "1.0.0",
                "status": "nope",
                "schema": [
                    {
                        "name": "row",
                        "logicalType": "object",
                        "properties": [{"name": "id", "logicalType": "string"}],
                    }
                ],
            }
        )
    with pytest.raises(OdcsImportError, match="logical type"):
        import_odcs(
            {
                "apiVersion": "v3.1.0",
                "kind": "DataContract",
                "id": "x",
                "name": "X",
                "version": "1.0.0",
                "status": "draft",
                "schema": [
                    {
                        "name": "row",
                        "logicalType": "object",
                        "properties": [{"name": "id", "logicalType": "not-a-type"}],
                    }
                ],
            }
        )


def test_describe_inferred_from_contract_model_without_identity() -> None:
    class Manual(ContractModel):
        value: int

    described = describe_contract(Manual)
    assert described.fidelity.status == FidelityStatus.NORMALIZED
    assert any(f.code == "IDENTITY_INFERRED" for f in described.fidelity.findings)
