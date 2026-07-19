"""Tests for ODCS export."""

from pathlib import Path

import yaml

from contractmodel.adapters.odcs import export_odcs, import_odcs

EXAMPLES_DIR = Path(__file__).resolve().parents[2] / "examples"


def test_export_customer_events_odcs() -> None:
    path = EXAMPLES_DIR / "customer_events.odcs.yaml"
    with path.open() as f:
        data = yaml.safe_load(f)

    contract = import_odcs(data)
    exported = export_odcs(contract)

    assert exported["id"] == "customer-events"
    assert exported["name"] == "Customer Events"
    assert exported["version"] == "1.0.0"
    assert exported["team"]["name"] == "customer-platform"
    assert len(exported["schema"]) == 1
    props = exported["schema"][0]["properties"]
    assert len(props) == 4

    event_type = next(item for item in props if item["name"] == "event_type")
    assert event_type["logicalType"] == "string"
    enum_prop = next(
        item for item in event_type["customProperties"] if item["property"] == "enum"
    )
    assert enum_prop["value"] == ["created", "updated", "deleted"]
