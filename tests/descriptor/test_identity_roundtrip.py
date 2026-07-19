"""Identity-preserving round trips and nested ODCS."""

from __future__ import annotations

from contractmodel import (
    DataContract,
    describe_contract,
    export_stability,
    fingerprint_contract,
    is_contract_model,
)
from contractmodel.export.registry import ExportStability


def test_odcs_pydantic_roundtrip_preserves_identity_and_nested() -> None:
    data = {
        "apiVersion": "v3.1.0",
        "kind": "DataContract",
        "id": "nested-contract",
        "name": "Nested Contract",
        "version": "3.2.1",
        "schema": [
            {
                "name": "customer",
                "logicalType": "object",
                "required": True,
                "properties": [
                    {"name": "id", "logicalType": "string", "required": True},
                    {
                        "name": "tags",
                        "logicalType": "array",
                        "items": {"name": "item", "logicalType": "string"},
                    },
                ],
            }
        ],
    }
    original = DataContract.from_odcs_dict(data)
    assert original.fields[0].children[0].name == "id"
    assert original.fields[0].children[1].logical_type.value == "array"

    model = original.to_pydantic()
    assert is_contract_model(model)
    assert model.__contract_id__ == "nested-contract"
    assert model.__contract_version__ == "3.2.1"
    assert model.__contract_fingerprint__ == fingerprint_contract(original.ccm)

    restored = DataContract.from_pydantic(model)
    assert restored.contract_id == "nested-contract"
    assert restored.version == "3.2.1"
    assert restored.fields[0].children[0].name == "id"
    assert fingerprint_contract(restored.ccm) == fingerprint_contract(original.ccm)

    exported = restored.to_odcs()
    assert exported["id"] == "nested-contract"
    assert exported["schema"][0]["properties"][0]["name"] == "id"


def test_integrator_surface_uses_only_top_level_apis() -> None:
    """ETLantic-style analysis without model_fields or private limits."""
    contract = DataContract.from_odcs_dict(
        {
            "apiVersion": "v3.1.0",
            "kind": "DataContract",
            "id": "integrator",
            "name": "Integrator",
            "version": "1.0.0",
            "schema": [
                {
                    "name": "email",
                    "logicalType": "email",
                    "required": True,
                    "nullable": False,
                }
            ],
        }
    )
    descriptor = describe_contract(contract)
    assert descriptor.identity.contract_id == "integrator"
    assert descriptor.schema_view.fields[0].nullable is False
    assert descriptor.schema_view.fields[0].required is True
    assert len(descriptor.fingerprint) == 64
    assert export_stability("odcs") is ExportStability.STABLE
    assert export_stability("rdf") is ExportStability.EXPERIMENTAL
