"""Shared canonical value encoding for wire JSON and fingerprints."""

from __future__ import annotations

from decimal import Decimal
from enum import Enum
from typing import Any


def canonicalize_number(value: float | int | Decimal) -> str:
    """Return a stable decimal string for fingerprint participation.

    Integers, floats, and Decimals that represent the same finite value canonicalize
    to the same string. Non-finite values raise ``ValueError``.
    """
    if isinstance(value, bool):
        msg = f"Boolean is not a numeric fingerprint value: {value!r}"
        raise TypeError(msg)
    if isinstance(value, float):
        if value != value or value in (float("inf"), float("-inf")):  # noqa: PLR0124
            msg = f"Non-finite float cannot be canonicalized: {value!r}"
            raise ValueError(msg)
        decimal_value = Decimal(format(value, ".15g"))
    elif isinstance(value, int):
        decimal_value = Decimal(value)
    elif isinstance(value, Decimal):
        if not value.is_finite():
            msg = f"Non-finite Decimal cannot be canonicalized: {value!r}"
            raise ValueError(msg)
        decimal_value = value
    else:
        msg = f"Unsupported numeric type: {type(value)!r}"
        raise TypeError(msg)

    normalized = decimal_value.normalize()
    text = format(normalized, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    if text in {"", "-"}:
        return "0"
    if text == "-0":
        return "0"
    return text


def canonicalize_jsonable(
    value: Any,
    *,
    sort_object_keys: bool = False,
    numbers_as_strings: bool = False,
) -> Any:
    """Recursively convert values to JSON-safe canonical forms."""
    if value is None or isinstance(value, (bool, str)):
        return value
    if isinstance(value, (int, float, Decimal)) and not isinstance(value, bool):
        if numbers_as_strings:
            return canonicalize_number(value)
        if isinstance(value, float):
            if value != value or value in (float("inf"), float("-inf")):  # noqa: PLR0124
                msg = f"Non-finite float cannot be canonicalized: {value!r}"
                raise ValueError(msg)
            return value
        if isinstance(value, Decimal):
            if not value.is_finite():
                msg = f"Non-finite Decimal cannot be canonicalized: {value!r}"
                raise ValueError(msg)
            return canonicalize_number(value)
        return value
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        items: list[tuple[Any, Any]] = list(value.items())
        if sort_object_keys:
            items = sorted(items, key=lambda kv: str(kv[0]))
        return {
            str(k): canonicalize_jsonable(
                v,
                sort_object_keys=sort_object_keys,
                numbers_as_strings=numbers_as_strings,
            )
            for k, v in items
        }
    if isinstance(value, (list, tuple)):
        return [
            canonicalize_jsonable(
                item,
                sort_object_keys=sort_object_keys,
                numbers_as_strings=numbers_as_strings,
            )
            for item in value
        ]
    if hasattr(value, "model_dump"):
        return canonicalize_jsonable(
            value.model_dump(mode="python", by_alias=True),
            sort_object_keys=sort_object_keys,
            numbers_as_strings=numbers_as_strings,
        )
    msg = f"Unsupported canonical value type: {type(value)!r}"
    raise TypeError(msg)
