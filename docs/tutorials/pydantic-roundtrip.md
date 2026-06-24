# Pydantic round-trip

Generate a Pydantic model from a contract, then map a model class back into the CCM.

## Contract → Pydantic

```python
from contractmodel import DataContract, ValidationMode
from contractmodel.examples import load_example

contract = load_example("customer_events.odcs.yaml")
CustomerEvent = contract.to_pydantic()

record = CustomerEvent(
    event_id="550e8400-e29b-41d4-a716-446655440000",
    customer_id="C123",
    event_timestamp="2026-06-23T12:00:00",
    event_type="created",
)
print(record.model_dump())
```

Reuse the model class — `to_pydantic()` is cached per contract instance.

## Pydantic → contract

```python
from pydantic import BaseModel, Field

class Order(BaseModel):
    order_id: str = Field(min_length=1)
    amount: float = Field(ge=0)

contract = DataContract.from_pydantic(Order, name="orders")
print(contract.name)
print([f.name for f in contract.fields])
```

## Validate with the contract facade

```python
result = contract.validate_record(
    {"order_id": "A1", "amount": 42.0},
    mode=ValidationMode.STRICT,
)
assert result.success
```
