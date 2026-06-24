"""Tests for validation model caching."""

from contractmodel.adapters.pydantic import get_pydantic_model
from contractmodel.core.ccm import CanonicalContract
from contractmodel.core.types import ValidationMode
from contractmodel.validation import engine as validation_engine


def _contract() -> CanonicalContract:
    return CanonicalContract.model_validate(
        {
            "contract_id": "cache",
            "name": "Cache",
            "version": "1.0.0",
            "schema": {
                "fields": [
                    {"name": "id", "logical_type": "string", "required": True},
                ]
            },
        }
    )


def test_validation_reuses_cached_pydantic_model() -> None:
    get_pydantic_model.cache_clear()
    contract = _contract()
    model1 = validation_engine._validation_model(contract, mode=ValidationMode.STRICT)
    model2 = validation_engine._validation_model(contract, mode=ValidationMode.STRICT)
    assert model1 is model2


def test_validate_records_builds_model_once() -> None:
    get_pydantic_model.cache_clear()
    contract = _contract()
    records = [{"id": "a"}, {"id": "b"}]
    result = validation_engine.validate_records(contract, records)
    assert result.success is True
    assert result.metrics["records_total"] == 2
