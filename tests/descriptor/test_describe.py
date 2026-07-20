"""Immutable descriptor tests."""

from __future__ import annotations

from contractmodel import (
    CanonicalContract,
    ContractField,
    ContractSchema,
    DataContract,
    LogicalType,
    describe_contract,
    fingerprint_contract,
)
from contractmodel.descriptor.models import FidelityStatus


def test_describe_contract_is_immutable_after_ccm_mutation() -> None:
    ccm = CanonicalContract(
        contract_id="c1",
        name="C1",
        version="1.0.0",
        schema=ContractSchema(
            fields=[ContractField(name="id", logical_type=LogicalType.STRING)]
        ),
    )
    descriptor = describe_contract(ccm)
    original_fp = descriptor.fingerprint

    ccm.contract_id = "mutated"
    ccm.contract_schema.fields[0].nullable = True
    ccm.description = "changed"

    assert descriptor.identity.contract_id == "c1"
    assert descriptor.fingerprint == original_fp
    assert descriptor.schema_view.fields[0].nullable is False


def test_data_contract_describe_maps_lossy_import() -> None:
    data = {
        "apiVersion": "v3.1.0",
        "kind": "DataContract",
        "id": "events",
        "name": "Events",
        "version": "1.0.0",
        "status": "draft",
        "team": {
            "name": "platform",
            "members": [
                {
                    "username": "alice",
                    "role": "owner",
                    "dateIn": "2024-01-01",
                }
            ],
        },
        "support": [{"channel": "email", "url": "https://example.com/help"}],
        "schema": [
            {
                "name": "events",
                "logicalType": "object",
                "properties": [{"name": "id", "logicalType": "string", "required": True}],
            }
        ],
    }
    contract = DataContract.from_odcs_dict(data)
    descriptor = contract.describe()
    assert descriptor.fidelity.status == FidelityStatus.LOSSY
    assert any(f.code == "ODCS_LOSSY_IMPORT" for f in descriptor.fidelity.findings)
    assert descriptor.fingerprint == fingerprint_contract(contract.ccm)


def test_data_contract_describe_standard_odcs_is_not_lossy() -> None:
    data = {
        "apiVersion": "v3.1.0",
        "kind": "DataContract",
        "id": "events",
        "name": "Events",
        "version": "1.0.0",
        "status": "draft",
        "team": {"name": "platform"},
        "support": [{"channel": "email", "url": "mailto:a@example.com"}],
        "schema": [
            {
                "name": "events",
                "logicalType": "object",
                "properties": [{"name": "id", "logicalType": "string", "required": True}],
            }
        ],
    }
    contract = DataContract.from_odcs_dict(data)
    descriptor = contract.describe()
    assert descriptor.fidelity.status != FidelityStatus.LOSSY
    assert not any(f.code == "ODCS_LOSSY_IMPORT" for f in descriptor.fidelity.findings)
