"""Tests for CCM serialization."""

from pathlib import Path

import yaml

from contractmodel.core.ccm import CanonicalContract

EXAMPLES_DIR = Path(__file__).resolve().parents[2] / "examples"


def test_load_customer_events_ccm_yaml() -> None:
    path = EXAMPLES_DIR / "customer_events.ccm.yaml"
    with path.open() as f:
        data = yaml.safe_load(f)

    contract = CanonicalContract.model_validate(data)

    assert contract.contract_id == "customer-events"
    assert contract.name == "Customer Events"
    assert contract.version == "1.0.0"
    assert contract.kind.value == "dataset"
    assert contract.status.value == "active"
    assert contract.ownership is not None
    assert contract.ownership.team == "customer-platform"
    assert len(contract.contract_schema.fields) == 4
    assert contract.contract_schema.primary_key == ["event_id"]

    event_type = next(f for f in contract.contract_schema.fields if f.name == "event_type")
    assert event_type.logical_type.value == "enum"
    assert event_type.constraints.enum_values == ["created", "updated", "deleted"]

    customer_id = next(f for f in contract.contract_schema.fields if f.name == "customer_id")
    assert customer_id.semantic is not None
    assert customer_id.semantic.ontology_class == "cdao:Person"


def test_ccm_yaml_roundtrip() -> None:
    path = EXAMPLES_DIR / "customer_events.ccm.yaml"
    with path.open() as f:
        data = yaml.safe_load(f)

    contract = CanonicalContract.model_validate(data)
    roundtripped = CanonicalContract.model_validate(
        contract.model_dump(mode="json", by_alias=True)
    )

    assert roundtripped == contract


def test_ccm_schema_alias_in_dump() -> None:
    path = EXAMPLES_DIR / "customer_events.ccm.yaml"
    with path.open() as f:
        data = yaml.safe_load(f)

    contract = CanonicalContract.model_validate(data)
    dumped = contract.model_dump(by_alias=True)

    assert "schema" in dumped
    assert "contract_schema" not in dumped


def test_ccm_json_roundtrip() -> None:
    path = EXAMPLES_DIR / "customer_events.ccm.yaml"
    with path.open() as f:
        data = yaml.safe_load(f)

    contract = CanonicalContract.model_validate(data)
    json_data = contract.model_dump_json(by_alias=True)
    roundtripped = CanonicalContract.model_validate_json(json_data)

    assert roundtripped == contract
