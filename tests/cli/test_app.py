"""Tests for CLI."""

import json
from pathlib import Path

from typer.testing import CliRunner

from contractmodel.cli.app import app

runner = CliRunner()
EXAMPLES_DIR = Path(__file__).resolve().parents[2] / "examples"


def test_doctor_command() -> None:
    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 0
    assert "Python:" in result.stdout


def test_validate_contract_only() -> None:
    contract_path = EXAMPLES_DIR / "customer_events.odcs.yaml"
    result = runner.invoke(app, ["validate", str(contract_path)])
    assert result.exit_code == 0
    assert "valid" in result.stdout.lower()


def test_validate_json_data_failure() -> None:
    contract_path = EXAMPLES_DIR / "customer_events.odcs.yaml"
    data_path = Path(__file__).parent / "invalid.json"
    data_path.write_text(json.dumps({"event_id": "bad"}))
    try:
        result = runner.invoke(app, ["validate", str(contract_path), str(data_path)])
        assert result.exit_code == 1
    finally:
        data_path.unlink(missing_ok=True)


def test_diff_breaking_exit_code() -> None:
    old_path = EXAMPLES_DIR / "customer_events.odcs.yaml"
    new_path = Path(__file__).parent / "reduced.yaml"
    new_path.write_text(
        "apiVersion: v3.0.0\n"
        "kind: DataContract\n"
        "id: customer-events\n"
        "name: Customer Events\n"
        "version: 2.0.0\n"
        "schema:\n"
        "  - name: event_id\n"
        "    logicalType: uuid\n"
        "    required: true\n"
    )
    try:
        result = runner.invoke(app, ["diff", str(old_path), str(new_path)])
        assert result.exit_code == 1
        assert "Breaking" in result.stdout or "BREAKING" in result.stdout
    finally:
        new_path.unlink(missing_ok=True)


def test_generate_pydantic(tmp_path: Path) -> None:
    contract_path = EXAMPLES_DIR / "customer_events.odcs.yaml"
    output = tmp_path / "models.py"
    result = runner.invoke(
        app,
        ["generate", "pydantic", str(contract_path), "--output", str(output)],
    )
    assert result.exit_code == 0
    assert output.exists()
    assert "ContractModel" in output.read_text()


def test_init_command(tmp_path: Path) -> None:
    path = tmp_path / "contract.yaml"
    result = runner.invoke(app, ["init", str(path)])
    assert result.exit_code == 0
    assert path.exists()


def test_export_markdown() -> None:
    contract_path = EXAMPLES_DIR / "customer_events.odcs.yaml"
    result = runner.invoke(app, ["export", str(contract_path), "--to", "markdown"])
    assert result.exit_code == 0
    assert "# Customer Events" in result.stdout
