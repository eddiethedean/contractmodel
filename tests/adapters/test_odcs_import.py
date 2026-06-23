"""Tests for ODCS import."""

from pathlib import Path

import yaml

from contractmodel.adapters.odcs import import_odcs
from contractmodel.core.types import LogicalType

EXAMPLES_DIR = Path(__file__).resolve().parents[2] / "examples"


def test_import_customer_events_odcs() -> None:
    path = EXAMPLES_DIR / "customer_events.odcs.yaml"
    with path.open() as f:
        data = yaml.safe_load(f)

    contract = import_odcs(data)

    assert contract.contract_id == "customer-events"
    assert contract.name == "Customer Events"
    assert contract.version == "1.0.0"
    assert contract.ownership is not None
    assert contract.ownership.team == "customer-platform"
    assert contract.ownership.contacts[0].email == "data-team@example.com"

    field_names = [field.name for field in contract.schema.fields]
    assert field_names == ["event_id", "customer_id", "event_timestamp", "event_type"]

    event_id = contract.schema.fields[0]
    assert event_id.logical_type == LogicalType.UUID

    event_type = contract.schema.fields[3]
    assert event_type.logical_type == LogicalType.ENUM
    assert event_type.constraints.enum_values == ["created", "updated", "deleted"]
