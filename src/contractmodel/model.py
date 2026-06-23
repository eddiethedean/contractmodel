"""Base model for generated contract Pydantic classes."""

from pydantic import BaseModel, ConfigDict


class ContractModel(BaseModel):
    """Base class for Pydantic models generated from contracts."""

    model_config = ConfigDict(extra="forbid")
