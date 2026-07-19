"""Tests for CCM wire schema and canonical dict helpers."""

from __future__ import annotations

from contractmodel import CanonicalContract, ContractField, ContractSchema, LogicalType
from contractmodel.versions import CCM_WIRE_VERSION
from contractmodel.wire import canonical_ccm_dict, export_ccm_json_schema, load_ccm_json_schema


def _sample_contract() -> CanonicalContract:
    return CanonicalContract(
        contract_id="demo",
        name="Demo",
        version="1.2.3",
        schema=ContractSchema(
            fields=[
                ContractField(name="id", logical_type=LogicalType.STRING),
                ContractField(
                    name="address",
                    logical_type=LogicalType.OBJECT,
                    children=[
                        ContractField(name="city", logical_type=LogicalType.STRING),
                    ],
                ),
            ]
        ),
    )


def test_load_ccm_json_schema_has_wire_id() -> None:
    schema = load_ccm_json_schema()
    assert schema["$id"] == "https://contractmodel.dev/schemas/ccm/1"
    assert schema["title"] == CCM_WIRE_VERSION
    assert "schema" in schema["required"]


def test_export_ccm_json_schema_is_copy() -> None:
    first = export_ccm_json_schema()
    second = export_ccm_json_schema()
    first["title"] = "mutated"
    assert second["title"] == CCM_WIRE_VERSION


def test_canonical_ccm_dict_uses_schema_alias_and_wire_version() -> None:
    wire = canonical_ccm_dict(_sample_contract())
    assert wire["ccm_wire_version"] == CCM_WIRE_VERSION
    assert "schema" in wire
    assert "contract_schema" not in wire
    assert wire["schema"]["fields"][1]["children"][0]["name"] == "city"
