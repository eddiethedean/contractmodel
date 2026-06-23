"""Additional pydantic adapter coverage."""

from enum import Enum

from pydantic import BaseModel, Field

from contractmodel.adapters.pydantic import contract_from_pydantic, generate_pydantic_model
from contractmodel.core.ccm import CanonicalContract
from contractmodel.core.types import LogicalType


def test_field_with_default_and_constraints() -> None:
    contract = CanonicalContract.model_validate(
        {
            "contract_id": "d",
            "name": "D",
            "version": "1.0.0",
            "schema": {
                "fields": [
                    {
                        "name": "label",
                        "logical_type": "string",
                        "required": False,
                        "nullable": False,
                        "default": "default",
                        "constraints": {"min_length": 1, "max_length": 10, "pattern": "^a"},
                    }
                ]
            },
        }
    )
    model = generate_pydantic_model(contract)
    assert model().label == "default"


def test_array_without_children_and_map_without_children() -> None:
    contract = CanonicalContract.model_validate(
        {
            "contract_id": "loose",
            "name": "Loose",
            "version": "1.0.0",
            "schema": {
                "fields": [
                    {"name": "items", "logical_type": "array"},
                    {"name": "attrs", "logical_type": "map"},
                ]
            },
        }
    )
    model = generate_pydantic_model(contract)
    instance = model(items=[], attrs={})
    assert instance.items == []


def test_reverse_nullable_union_and_enum_metadata() -> None:
    class Color(str, Enum):
        RED = "red"

    class Item(BaseModel):
        name: str | None
        color: Color
        score: int = Field(ge=1, le=9, min_length=1, max_length=3, pattern="^[0-9]+$")

    contract = contract_from_pydantic(Item)
    name_field = next(f for f in contract.contract_schema.fields if f.name == "name")
    assert name_field.nullable is True
    color_field = next(f for f in contract.contract_schema.fields if f.name == "color")
    assert color_field.logical_type == LogicalType.ENUM
    score_field = next(f for f in contract.contract_schema.fields if f.name == "score")
    assert score_field.constraints.min_value == 1
