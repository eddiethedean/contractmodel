"""Pydantic model generation and reverse adapter."""

from __future__ import annotations

import datetime
import re
import uuid
from decimal import Decimal
from enum import Enum
from functools import lru_cache
from typing import Any, cast, get_args, get_origin

from pydantic import BaseModel, ConfigDict, EmailStr, Field, create_model
from pydantic.networks import AnyUrl

from contractmodel.core.ccm import CanonicalContract, ContractField, ContractSchema
from contractmodel.core.constraints import FieldConstraints
from contractmodel.core.types import LogicalType, ValidationMode
from contractmodel.model import ContractModel


def mode_to_generation_options(mode: ValidationMode) -> tuple[bool, bool]:
    """Map a validation mode to Pydantic model generation flags."""
    schema_only = mode == ValidationMode.SCHEMA_ONLY
    forbid_extra = mode == ValidationMode.STRICT
    return schema_only, forbid_extra


@lru_cache(maxsize=128)
def get_pydantic_model(
    contract_json: str,
    class_name: str | None,
    schema_only: bool,
    forbid_extra: bool,
) -> type[BaseModel]:
    """Return a cached Pydantic model for a contract and generation options."""
    contract = CanonicalContract.model_validate_json(contract_json)
    return generate_pydantic_model(
        contract,
        class_name=class_name,
        schema_only=schema_only,
        forbid_extra=forbid_extra,
    )


def generate_pydantic_model(
    contract: CanonicalContract,
    *,
    class_name: str | None = None,
    schema_only: bool = False,
    forbid_extra: bool = True,
) -> type[BaseModel]:
    """Generate a Pydantic V2 model from a CanonicalContract."""
    model_name = class_name or _to_class_name(contract.name)
    field_defs = _build_field_definitions(
        contract.contract_schema.fields,
        model_name,
        schema_only=schema_only,
    )
    if forbid_extra:
        base: type[BaseModel] = ContractModel
    else:
        base = type(
            f"{model_name}PermissiveBase",
            (ContractModel,),
            {"model_config": ConfigDict(extra="ignore")},
        )
    return create_model(
        model_name,
        __base__=base,
        **field_defs,
    )


def contract_from_pydantic(
    model: type[BaseModel],
    *,
    name: str | None = None,
) -> CanonicalContract:
    """Convert a Pydantic model into a CanonicalContract."""
    contract_name = name or model.__name__
    contract_id = _to_contract_id(contract_name)
    fields = [
        _field_from_pydantic_field(field_name, field_info)
        for field_name, field_info in model.model_fields.items()
    ]

    return CanonicalContract(
        contract_id=contract_id,
        name=contract_name,
        version="1.0.0",
        schema=ContractSchema(fields=fields),
    )


def _build_field_definitions(
    fields: list[ContractField],
    model_name: str,
    *,
    schema_only: bool = False,
) -> dict[str, Any]:
    field_defs: dict[str, Any] = {}
    for field in fields:
        field_defs[field.name] = _build_single_field(field, model_name, schema_only=schema_only)
    return field_defs


def _build_single_field(
    field: ContractField,
    model_name: str,
    *,
    schema_only: bool = False,
) -> Any:
    python_type = _logical_type_to_python(field, model_name, schema_only=schema_only)
    field_kwargs = {} if schema_only else _constraints_to_field_kwargs(field.constraints)

    annotation, default = _apply_required_nullable(field, python_type)

    if default is ...:
        if field_kwargs:
            return (annotation, Field(**field_kwargs))
        return annotation

    if field_kwargs:
        return (annotation, Field(default=default, **field_kwargs))
    return (annotation, default)


def _apply_required_nullable(
    field: ContractField,
    python_type: Any,
) -> tuple[Any, Any]:
    if field.required and not field.nullable:
        return python_type, ...
    if field.required and field.nullable:
        return python_type | None, ...
    if not field.required and not field.nullable:
        if field.default is not None:
            return python_type, field.default
        return python_type, ...
    return python_type | None, None if field.default is None else field.default


def _logical_type_to_python(
    field: ContractField,
    model_name: str,
    *,
    schema_only: bool = False,
) -> Any:
    logical_type = field.logical_type

    if logical_type == LogicalType.ENUM:
        return _create_enum_class(field, model_name)

    if logical_type == LogicalType.OBJECT:
        nested_name = f"{model_name}{_to_class_name(field.name)}"
        nested_fields = _build_field_definitions(
            field.children,
            nested_name,
            schema_only=schema_only,
        )
        return cast(
            type[BaseModel],
            create_model(nested_name, __base__=ContractModel, **nested_fields),
        )

    if logical_type == LogicalType.ARRAY:
        if field.children:
            child_name = f"{model_name}{_to_class_name(field.name)}Item"
            item_type = _logical_type_to_python(
                field.children[0],
                child_name,
                schema_only=schema_only,
            )
        else:
            item_type = Any
        return list[item_type]  # type: ignore[valid-type]

    if logical_type == LogicalType.MAP:
        if field.children:
            child_name = f"{model_name}{_to_class_name(field.name)}Value"
            value_type = _logical_type_to_python(
                field.children[0],
                child_name,
                schema_only=schema_only,
            )
        else:
            value_type = Any
        return dict[str, value_type]  # type: ignore[valid-type]

    mapping: dict[LogicalType, Any] = {
        LogicalType.STRING: str,
        LogicalType.INTEGER: int,
        LogicalType.NUMBER: float,
        LogicalType.DECIMAL: Decimal,
        LogicalType.BOOLEAN: bool,
        LogicalType.DATE: datetime.date,
        LogicalType.TIME: datetime.time,
        LogicalType.DATETIME: datetime.datetime,
        LogicalType.DURATION: datetime.timedelta,
        LogicalType.BINARY: bytes,
        LogicalType.UUID: uuid.UUID,
        LogicalType.URI: AnyUrl,
        LogicalType.EMAIL: EmailStr,
        LogicalType.ANY: Any,
    }
    return mapping.get(logical_type, str)


def _create_enum_class(field: ContractField, model_name: str) -> type[Enum]:
    enum_name = f"{model_name}{_to_class_name(field.name)}Enum"
    values = field.constraints.enum_values or []
    members: dict[str, Any] = {}
    used_names: set[str] = set()
    for index, value in enumerate(values):
        base = re.sub(r"[^a-zA-Z0-9_]", "_", str(value).upper()).strip("_")
        if not base or base[0].isdigit():
            base = f"VALUE_{index}"
        name = base
        suffix = 1
        while name in used_names:
            name = f"{base}_{suffix}"
            suffix += 1
        used_names.add(name)
        members[name] = value
    if not members:
        msg = f"ENUM field '{field.name}' must have non-empty enum_values"
        raise ValueError(msg)
    return cast(type[Enum], Enum(enum_name, members))


def _constraints_to_field_kwargs(constraints: FieldConstraints) -> dict[str, Any]:
    kwargs: dict[str, Any] = {}
    if constraints.min_value is not None:
        kwargs["ge"] = constraints.min_value
    if constraints.max_value is not None:
        kwargs["le"] = constraints.max_value
    if constraints.min_length is not None:
        kwargs["min_length"] = constraints.min_length
    if constraints.max_length is not None:
        kwargs["max_length"] = constraints.max_length
    if constraints.pattern is not None:
        kwargs["pattern"] = constraints.pattern
    return kwargs


def _field_from_pydantic_field(field_name: str, field_info: Any) -> ContractField:
    annotation = field_info.annotation
    required = field_info.is_required()
    default = None if field_info.is_required() else field_info.default
    nullable = _is_nullable(annotation)
    constraints = _constraints_from_field_info(field_info)

    logical_type, children, inferred = _python_type_to_logical(annotation, field_name)
    if not constraints.min_value and inferred.min_value is None:
        constraints = inferred
    elif inferred.enum_values:
        constraints = FieldConstraints(
            min_value=constraints.min_value or inferred.min_value,
            max_value=constraints.max_value or inferred.max_value,
            min_length=constraints.min_length or inferred.min_length,
            max_length=constraints.max_length or inferred.max_length,
            pattern=constraints.pattern or inferred.pattern,
            enum_values=inferred.enum_values,
        )

    return ContractField(
        name=field_name,
        logical_type=logical_type,
        required=required,
        nullable=nullable,
        default=default,
        constraints=constraints,
        children=children,
    )


def _constraints_from_field_info(field_info: Any) -> FieldConstraints:
    metadata = getattr(field_info, "metadata", [])
    kwargs: dict[str, Any] = {}
    for item in metadata:
        if hasattr(item, "ge"):
            kwargs["min_value"] = item.ge
        if hasattr(item, "le"):
            kwargs["max_value"] = item.le
        if hasattr(item, "min_length"):
            kwargs["min_length"] = item.min_length
        if hasattr(item, "max_length"):
            kwargs["max_length"] = item.max_length
        if hasattr(item, "pattern"):
            kwargs["pattern"] = item.pattern
    return FieldConstraints(**kwargs)


def _is_nullable(annotation: Any) -> bool:
    origin = get_origin(annotation)
    if origin is not None:
        args = get_args(annotation)
        return type(None) in args
    return False


def _python_type_to_logical(
    annotation: Any,
    field_name: str,
) -> tuple[LogicalType, list[ContractField], FieldConstraints]:
    if annotation is EmailStr:
        return LogicalType.EMAIL, [], FieldConstraints()
    if annotation is AnyUrl:
        return LogicalType.URI, [], FieldConstraints()

    origin = get_origin(annotation)
    args = get_args(annotation)

    if origin is not None and type(None) in args:
        non_none = [a for a in args if a is not type(None)]
        if len(non_none) == 1:
            return _python_type_to_logical(non_none[0], field_name)

    if origin is list:
        item_type = args[0] if args else Any
        lt, children, constraints = _python_type_to_logical(item_type, f"{field_name}_item")
        child = ContractField(
            name="item",
            logical_type=lt,
            children=children,
            constraints=constraints,
        )
        return LogicalType.ARRAY, [child], FieldConstraints()

    if origin is dict:
        value_type = args[1] if len(args) > 1 else Any
        lt, children, constraints = _python_type_to_logical(value_type, f"{field_name}_value")
        child = ContractField(
            name="value",
            logical_type=lt,
            children=children,
            constraints=constraints,
        )
        return LogicalType.MAP, [child], FieldConstraints()

    if isinstance(annotation, type) and issubclass(annotation, Enum):
        return (
            LogicalType.ENUM,
            [],
            FieldConstraints(enum_values=[member.value for member in annotation]),
        )

    if isinstance(annotation, type) and issubclass(annotation, BaseModel):
        children = [
            _field_from_pydantic_field(name, info)
            for name, info in annotation.model_fields.items()
        ]
        return LogicalType.OBJECT, children, FieldConstraints()

    type_map: dict[type, LogicalType] = {
        str: LogicalType.STRING,
        int: LogicalType.INTEGER,
        float: LogicalType.NUMBER,
        Decimal: LogicalType.DECIMAL,
        bool: LogicalType.BOOLEAN,
        datetime.date: LogicalType.DATE,
        datetime.time: LogicalType.TIME,
        datetime.datetime: LogicalType.DATETIME,
        datetime.timedelta: LogicalType.DURATION,
        bytes: LogicalType.BINARY,
        uuid.UUID: LogicalType.UUID,
    }
    if annotation in type_map:
        return type_map[annotation], [], FieldConstraints()

    return LogicalType.ANY, [], FieldConstraints()


def _to_class_name(name: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", " ", name).title().replace(" ", "")
    return cleaned or "Contract"


def _to_contract_id(name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "-", name.strip().lower()).strip("-") or "contract"
