"""Pre-0.2.0 release regression fixes."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
import yaml

from contractmodel import DataContract, LoadingPolicy, LogicalType
from contractmodel.adapters.odcs import export_odcs, import_odcs
from contractmodel.core.ccm import CanonicalContract, ContractField, ContractSchema
from contractmodel.policy import LoadingPolicyError, resolve_contract_path


def test_save_auto_selects_odcs_yaml(tmp_path: Path) -> None:
    contract = DataContract.from_ccm(
        CanonicalContract(
            contract_id="auto",
            name="Auto",
            version="1.0.0",
            schema=ContractSchema(
                fields=[ContractField(name="id", logical_type=LogicalType.STRING)]
            ),
        )
    )
    path = tmp_path / "saved.odcs.yaml"
    contract.save(path)
    data = yaml.safe_load(path.read_text())
    assert data["id"] == "auto"
    assert "contract_id" not in data
    assert data["schema"][0]["logicalType"] == "object"


def test_macos_tmp_path_is_allowed(tmp_path: Path) -> None:
    if sys.platform != "darwin":
        pytest.skip("macOS /tmp alias check")
    source = tmp_path / "c.yaml"
    source.write_text(
        "contract_id: x\nname: X\nversion: 1.0.0\nschema:\n  fields: []\n",
        encoding="utf-8",
    )
    # /tmp resolves through a Darwin convenience symlink.
    linked = Path("/tmp") / f"contractmodel-release-{source.name}"
    try:
        linked.write_bytes(source.read_bytes())
        resolved = resolve_contract_path(linked)
        assert resolved.is_file()
        loaded = DataContract.load(linked)
        assert loaded.contract_id == "x"
    finally:
        linked.unlink(missing_ok=True)


def test_intermediate_user_symlink_still_blocked(tmp_path: Path) -> None:
    real_dir = tmp_path / "real"
    real_dir.mkdir()
    contract_path = real_dir / "c.yaml"
    contract_path.write_text(
        "contract_id: x\nname: X\nversion: 1.0.0\nschema:\n  fields: []\n",
        encoding="utf-8",
    )
    link_dir = tmp_path / "link"
    try:
        link_dir.symlink_to(real_dir)
    except OSError:
        pytest.skip("symlinks unavailable")
    with pytest.raises(LoadingPolicyError, match="Symlink"):
        DataContract.load(
            link_dir / "c.yaml",
            policy=LoadingPolicy(follow_symlinks=False, approved_roots=(tmp_path,)),
        )


def test_map_field_exports_valid_odcs() -> None:
    contract = CanonicalContract(
        contract_id="maps",
        name="Maps",
        version="1.0.0",
        schema=ContractSchema(
            fields=[
                ContractField(
                    name="attrs",
                    logical_type=LogicalType.MAP,
                    children=[
                        ContractField(name="value", logical_type=LogicalType.STRING)
                    ],
                )
            ]
        ),
    )
    exported = export_odcs(contract)
    prop = exported["schema"][0]["properties"][0]
    assert prop["logicalType"] == "object"
    assert "items" not in prop
    roundtrip = import_odcs(exported)
    assert roundtrip.contract_schema.fields[0].logical_type == LogicalType.MAP


def test_binary_and_decimal_roundtrip() -> None:
    contract = CanonicalContract(
        contract_id="types",
        name="Types",
        version="1.0.0",
        schema=ContractSchema(
            fields=[
                ContractField(name="blob", logical_type=LogicalType.BINARY),
                ContractField(name="amount", logical_type=LogicalType.DECIMAL),
            ]
        ),
    )
    exported = export_odcs(contract)
    roundtrip = import_odcs(exported)
    types = {field.name: field.logical_type for field in roundtrip.contract_schema.fields}
    assert types["blob"] == LogicalType.BINARY
    assert types["amount"] == LogicalType.DECIMAL


def test_primary_key_and_physical_name_roundtrip() -> None:
    data = {
        "apiVersion": "v3.1.0",
        "kind": "DataContract",
        "id": "pk",
        "name": "Pk",
        "version": "1.0.0",
        "status": "draft",
        "schema": [
            {
                "name": "customers",
                "logicalType": "object",
                "physicalName": "customers_tbl",
                "properties": [
                    {
                        "name": "customer_id",
                        "logicalType": "string",
                        "required": True,
                        "primaryKey": True,
                        "physicalName": "cust_id",
                    }
                ],
            }
        ],
    }
    contract = import_odcs(data)
    assert contract.contract_schema.primary_key == ["customer_id"]
    assert contract.contract_schema.fields[0].extensions["physicalName"] == "cust_id"
    exported = export_odcs(contract)
    assert exported["schema"][0]["physicalName"] == "customers_tbl"
    assert exported["schema"][0]["properties"][0]["primaryKey"] is True
    assert exported["schema"][0]["properties"][0]["physicalName"] == "cust_id"


def test_mixed_schema_entries_are_not_dropped() -> None:
    data = {
        "apiVersion": "v3.1.0",
        "kind": "DataContract",
        "id": "mixed",
        "name": "Mixed",
        "version": "1.0.0",
        "status": "draft",
        "schema": [
            {
                "name": "customers",
                "logicalType": "object",
                "properties": [{"name": "id", "logicalType": "string"}],
            },
            {"name": "orphan", "logicalType": "string"},
        ],
    }
    contract = import_odcs(data)
    assert [field.name for field in contract.contract_schema.fields] == [
        "customers",
        "orphan",
    ]


def test_team_members_preserved_via_extension() -> None:
    data = {
        "apiVersion": "v3.1.0",
        "kind": "DataContract",
        "id": "team",
        "name": "Team",
        "version": "1.0.0",
        "status": "draft",
        "team": {
            "name": "Data Platform",
            "members": [
                {
                    "username": "jdoe",
                    "name": "Jane Doe",
                    "role": "owner",
                    "dateIn": "2024-01-01",
                }
            ],
        },
        "schema": [
            {
                "name": "row",
                "logicalType": "object",
                "properties": [{"name": "id", "logicalType": "string"}],
            }
        ],
    }
    contract = import_odcs(data)
    exported = export_odcs(contract)
    assert exported["team"]["members"][0]["username"] == "jdoe"


def test_normalize_bare_odcs_version() -> None:
    from contractmodel.versions import is_supported_odcs_version, normalize_odcs_api_version

    assert normalize_odcs_api_version("3.1.0") == "v3.1.0"
    assert is_supported_odcs_version("3.1.0")


def test_parse_invalid_odcs_text_raises_validation_error() -> None:
    from contractmodel.adapters.odcs_conformance import parse_and_validate_odcs
    from contractmodel.errors import OdcsValidationError

    with pytest.raises(OdcsValidationError):
        parse_and_validate_odcs("not: [valid")


def test_doctor_reports_versions() -> None:
    from typer.testing import CliRunner

    from contractmodel.cli.app import app

    result = CliRunner().invoke(app, ["doctor"])
    assert result.exit_code == 0
    assert "contractmodel:" in result.stdout
    assert "pyodcs:" in result.stdout


def test_cli_diff_odcs_flag() -> None:
    from typer.testing import CliRunner

    from contractmodel.cli.app import app
    from contractmodel.examples import example_path

    old = example_path("customer_events.odcs.yaml")
    runner = CliRunner()
    result = runner.invoke(app, ["diff", str(old), str(old), "--odcs"])
    assert result.exit_code == 0
    assert "Breaking: False" in result.stdout or "Breaking: false" in result.stdout.lower()


def test_cli_generate_emits_nested_classes(tmp_path: Path) -> None:
    from typer.testing import CliRunner

    from contractmodel.cli.app import app

    nested = tmp_path / "nested.ccm.yaml"
    nested.write_text(
        yaml.safe_dump(
            {
                "contract_id": "nested",
                "name": "Nested",
                "version": "1.0.0",
                "schema": {
                    "fields": [
                        {
                            "name": "address",
                            "logical_type": "object",
                            "children": [
                                {"name": "city", "logical_type": "string"},
                            ],
                        }
                    ]
                },
            }
        ),
        encoding="utf-8",
    )
    out = tmp_path / "models.py"
    runner = CliRunner()
    result = runner.invoke(
        app,
        ["generate", "pydantic", str(nested), "--output", str(out)],
    )
    assert result.exit_code == 0
    text = out.read_text()
    assert "class " in text
    assert "address:" in text
    # Generated module must be importable.
    compiled = compile(text, str(out), "exec")
    namespace: dict[str, object] = {}
    exec(compiled, namespace)
    assert "Nested" in namespace
