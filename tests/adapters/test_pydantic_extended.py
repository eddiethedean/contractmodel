"""Extended Pydantic adapter tests."""

from enum import Enum

from pydantic import BaseModel, EmailStr, Field
from pydantic.networks import AnyUrl

from contractmodel.adapters.pydantic import contract_from_pydantic, generate_pydantic_model
from contractmodel.core.ccm import CanonicalContract
from contractmodel.core.types import LogicalType


def test_enum_collision_names() -> None:
    contract = CanonicalContract.model_validate(
        {
            "contract_id": "enum",
            "name": "Enum",
            "version": "1.0.0",
            "schema": {
                "fields": [
                    {
                        "name": "status",
                        "logical_type": "enum",
                        "constraints": {"enum_values": ["a", "A", "1"]},
                    }
                ]
            },
        }
    )
    model = generate_pydantic_model(contract)
    assert model(status="a").status.value == "a"


def test_schema_only_and_permissive_extra() -> None:
    contract = CanonicalContract.model_validate(
        {
            "contract_id": "perm",
            "name": "Perm",
            "version": "1.0.0",
            "schema": {
                "fields": [
                    {
                        "name": "id",
                        "logical_type": "string",
                        "required": False,
                        "nullable": True,
                        "default": None,
                    }
                ]
            },
        }
    )
    model = generate_pydantic_model(contract, schema_only=True, forbid_extra=False)
    instance = model(id=None, extra_field="ok")
    assert instance.id is None


def test_optional_non_nullable_with_default() -> None:
    contract = CanonicalContract.model_validate(
        {
            "contract_id": "opt",
            "name": "Opt",
            "version": "1.0.0",
            "schema": {
                "fields": [
                    {
                        "name": "count",
                        "logical_type": "integer",
                        "required": False,
                        "nullable": False,
                        "default": 0,
                    }
                ]
            },
        }
    )
    model = generate_pydantic_model(contract)
    assert model().count == 0


def test_map_type_generation() -> None:
    contract = CanonicalContract.model_validate(
        {
            "contract_id": "map",
            "name": "Map",
            "version": "1.0.0",
            "schema": {
                "fields": [
                    {
                        "name": "attrs",
                        "logical_type": "map",
                        "children": [{"name": "value", "logical_type": "string"}],
                    }
                ]
            },
        }
    )
    model = generate_pydantic_model(contract)
    assert model(attrs={"k": "v"}).attrs == {"k": "v"}


def test_from_pydantic_email_url_enum_object() -> None:
    class Status(str, Enum):
        ACTIVE = "active"

    class Address(BaseModel):
        city: str

    class RichModel(BaseModel):
        email: EmailStr
        website: AnyUrl
        status: Status
        address: Address
        tags: list[str]
        attrs: dict[str, int]
        score: int = Field(ge=0, le=100)

    contract = contract_from_pydantic(RichModel, name="Rich")
    types = {field.name: field.logical_type for field in contract.contract_schema.fields}
    assert types["email"] == LogicalType.EMAIL
    assert types["website"] == LogicalType.URI
    assert types["status"] == LogicalType.ENUM
    assert types["address"] == LogicalType.OBJECT
    assert types["tags"] == LogicalType.ARRAY
    assert types["attrs"] == LogicalType.MAP
    score = next(field for field in contract.contract_schema.fields if field.name == "score")
    assert score.logical_type == LogicalType.INTEGER
