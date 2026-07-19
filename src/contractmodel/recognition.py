"""Recognition helpers for ContractModel types and annotations."""

from __future__ import annotations

from types import UnionType
from typing import Annotated, TypeGuard, Union, get_args, get_origin

from contractmodel.model import ContractModel


def is_contract_model(value: object) -> TypeGuard[type[ContractModel]]:
    """Return True when ``value`` is a ``ContractModel`` subclass."""
    return isinstance(value, type) and issubclass(value, ContractModel)


def resolve_contract_model(annotation: object) -> type[ContractModel] | None:
    """Resolve a ContractModel subclass from a type annotation if present."""
    if is_contract_model(annotation):
        return annotation

    origin = get_origin(annotation)
    if origin is Annotated:
        args = get_args(annotation)
        if args:
            return resolve_contract_model(args[0])
        return None

    if origin in (Union, UnionType):
        for arg in get_args(annotation):
            if arg is type(None):
                continue
            resolved = resolve_contract_model(arg)
            if resolved is not None:
                return resolved
        return None

    return None
