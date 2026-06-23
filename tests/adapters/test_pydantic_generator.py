"""Tests for Pydantic model generation."""

import uuid
from datetime import datetime
from pathlib import Path

import pytest
from pydantic import BaseModel, ValidationError

from contractmodel import DataContract
from contractmodel.adapters.pydantic import contract_from_pydantic, generate_pydantic_model
from contractmodel.core.ccm import CanonicalContract
from contractmodel.core.types import LogicalType

EXAMPLES_DIR = Path(__file__).resolve().parents[2] / "examples"


def test_generate_customer_events_model() -> None:
    contract = DataContract.from_odcs(EXAMPLES_DIR / "customer_events.odcs.yaml")
    model = contract.to_pydantic(class_name="CustomerEvent")

    instance = model(
        event_id=uuid.UUID("550e8400-e29b-41d4-a716-446655440000"),
        customer_id="C123",
        event_timestamp=datetime(2026, 6, 23, 12, 0, 0),
        event_type="created",
    )
    assert instance.customer_id == "C123"


def test_generated_model_rejects_invalid_enum() -> None:
    contract = DataContract.from_odcs(EXAMPLES_DIR / "customer_events.odcs.yaml")
    model = contract.to_pydantic()

    with pytest.raises(ValidationError):
        model(
            event_id=uuid.UUID("550e8400-e29b-41d4-a716-446655440000"),
            customer_id="C123",
            event_timestamp=datetime(2026, 6, 23, 12, 0, 0),
            event_type="invalid",
        )


def test_generate_nested_object_model() -> None:
    contract = CanonicalContract.model_validate(
        {
            "contract_id": "nested",
            "name": "Nested",
            "version": "1.0.0",
            "schema": {
                "fields": [
                    {
                        "name": "address",
                        "logical_type": "object",
                        "children": [
                            {"name": "city", "logical_type": "string"},
                            {"name": "zip", "logical_type": "integer"},
                        ],
                    }
                ]
            },
        }
    )
    model = generate_pydantic_model(contract)
    instance = model(address={"city": "Boston", "zip": 21})
    assert instance.address.city == "Boston"


def test_generate_array_model() -> None:
    contract = CanonicalContract.model_validate(
        {
            "contract_id": "tags",
            "name": "Tags",
            "version": "1.0.0",
            "schema": {
                "fields": [
                    {
                        "name": "labels",
                        "logical_type": "array",
                        "children": [{"name": "item", "logical_type": "string"}],
                    }
                ]
            },
        }
    )
    model = generate_pydantic_model(contract)
    instance = model(labels=["a", "b"])
    assert instance.labels == ["a", "b"]


def test_generate_constraints() -> None:
    contract = CanonicalContract.model_validate(
        {
            "contract_id": "constrained",
            "name": "Constrained",
            "version": "1.0.0",
            "schema": {
                "fields": [
                    {
                        "name": "score",
                        "logical_type": "integer",
                        "constraints": {"min_value": 0, "max_value": 100},
                    }
                ]
            },
        }
    )
    model = generate_pydantic_model(contract)
    with pytest.raises(ValidationError):
        model(score=101)


def test_from_pydantic_roundtrip() -> None:
    class SampleModel(BaseModel):
        id: str
        count: int = 0

    contract = contract_from_pydantic(SampleModel, name="Sample")
    assert contract.name == "Sample"
    assert len(contract.contract_schema.fields) == 2
    assert contract.contract_schema.fields[0].logical_type == LogicalType.STRING
    assert contract.contract_schema.fields[1].logical_type == LogicalType.INTEGER
