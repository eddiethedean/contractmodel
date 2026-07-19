"""Recognition helper tests."""

from __future__ import annotations

from typing import Annotated

from contractmodel import (
    ContractModel,
    DataContract,
    is_contract_model,
    resolve_contract_model,
)
from contractmodel.core.ccm import CanonicalContract, ContractField, ContractSchema
from contractmodel.core.types import LogicalType


def test_is_and_resolve_contract_model() -> None:
    contract = DataContract.from_ccm(
        CanonicalContract(
            contract_id="c",
            name="C",
            version="1.0.0",
            schema=ContractSchema(
                fields=[ContractField(name="id", logical_type=LogicalType.STRING)]
            ),
        )
    )
    model = contract.to_pydantic()
    assert is_contract_model(model)
    assert resolve_contract_model(model) is model
    assert resolve_contract_model(Annotated[model, "meta"]) is model
    assert resolve_contract_model(model | None) is model
    assert resolve_contract_model(str) is None
    assert is_contract_model(ContractModel)
