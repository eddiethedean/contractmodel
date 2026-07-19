"""Canonical JSON encoding and contract fingerprints.

Fingerprint participation (contractmodel.ccm/1):
- Identity: contract_id, version, name, kind
- Schema: fields recursively (name, logical_type, required, nullable, constraints,
  children, aliases), primary_key, indexes, schema constraints
- Extensions: only keys listed in ``FINGERPRINT_EXTENSION_NAMESPACES``

Excluded from fingerprints (present on descriptors but non-participating):
description, examples, default, status, ownership, quality, service_level,
lineage, semantics, governance, metadata, field description/examples/default/
semantic/metadata, and non-namespace extensions.

Numeric constraints are canonicalized via :func:`canonicalize_number` so
``1``, ``1.0``, and ``Decimal("1")`` share one fingerprint contribution.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from contractmodel.canonical import canonicalize_jsonable
from contractmodel.core.ccm import CanonicalContract, ContractField, ContractSchema, IndexSpec
from contractmodel.core.constraints import FieldConstraints, SchemaConstraint
from contractmodel.extensions import fingerprint_extensions


def _canon_value(value: Any) -> Any:
    return canonicalize_jsonable(value, sort_object_keys=True, numbers_as_strings=True)


def _constraints_payload(constraints: FieldConstraints) -> dict[str, Any]:
    return {
        "allowed_values": constraints.allowed_values,
        "custom": [
            {
                "expression": item.expression,
                "metadata": item.metadata,
                "name": item.name,
                "type": item.type,
            }
            for item in constraints.custom
        ],
        "disallowed_values": constraints.disallowed_values,
        "enum_values": constraints.enum_values,
        "immutable": constraints.immutable,
        "max_length": constraints.max_length,
        "max_value": constraints.max_value,
        "min_length": constraints.min_length,
        "min_value": constraints.min_value,
        "pattern": constraints.pattern,
        "unique": constraints.unique,
    }


def _field_payload(field: ContractField) -> dict[str, Any]:
    return {
        "aliases": list(field.aliases),
        "children": [_field_payload(child) for child in field.children],
        "constraints": _constraints_payload(field.constraints),
        "logical_type": field.logical_type.value,
        "name": field.name,
        "nullable": field.nullable,
        "required": field.required,
    }


def _index_payload(index: IndexSpec) -> dict[str, Any]:
    return {
        "fields": list(index.fields),
        "name": index.name,
        "unique": index.unique,
    }


def _schema_constraint_payload(constraint: SchemaConstraint) -> dict[str, Any]:
    return {
        "expression": constraint.expression,
        "fields": list(constraint.fields),
        "name": constraint.name,
        "type": constraint.type,
    }


def _schema_payload(schema: ContractSchema) -> dict[str, Any]:
    return {
        "constraints": [_schema_constraint_payload(c) for c in schema.constraints],
        "fields": [_field_payload(field) for field in schema.fields],
        "indexes": [_index_payload(index) for index in schema.indexes],
        "primary_key": list(schema.primary_key),
    }


def fingerprint_payload(contract: CanonicalContract) -> dict[str, Any]:
    """Build the JSON-serializable object that participates in the fingerprint."""
    return {
        "contract_id": contract.contract_id,
        "extensions": fingerprint_extensions(contract.extensions),
        "kind": contract.kind.value,
        "name": contract.name,
        "schema": _schema_payload(contract.contract_schema),
        "version": contract.version,
    }


def canonical_bytes(contract: CanonicalContract) -> bytes:
    """Return RFC-style canonical JSON bytes for fingerprinting."""
    payload = _canon_value(fingerprint_payload(contract))
    text = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return text.encode("utf-8")


def fingerprint_contract(contract: CanonicalContract) -> str:
    """Return the SHA-256 hex digest of the contract fingerprint payload."""
    return hashlib.sha256(canonical_bytes(contract)).hexdigest()
