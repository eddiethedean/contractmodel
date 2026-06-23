"""Extended CLI tests."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from contractmodel.cli.app import app
from contractmodel.registry.client import RegistryPublishResult

runner = CliRunner()
EXAMPLES_DIR = Path(__file__).resolve().parents[2] / "examples"


def test_init_fastapi_template(tmp_path: Path) -> None:
    app_dir = tmp_path / "myapp"
    result = runner.invoke(app, ["init", str(app_dir), "--template", "fastapi"])
    assert result.exit_code == 0
    assert (app_dir / "main.py").exists()
    assert (app_dir / "contract.yaml").exists()


def test_init_odcs_template(tmp_path: Path) -> None:
    path = tmp_path / "contract.yaml"
    result = runner.invoke(app, ["init", str(path), "--template", "odcs"])
    assert result.exit_code == 0
    assert "apiVersion" in path.read_text()


def test_init_existing_file(tmp_path: Path) -> None:
    path = tmp_path / "contract.yaml"
    path.write_text("existing")
    result = runner.invoke(app, ["init", str(path)])
    assert result.exit_code == 3


def test_validate_sarif_output() -> None:
    contract_path = EXAMPLES_DIR / "customer_events.odcs.yaml"
    data_path = Path(__file__).parent / "invalid.json"
    data_path.write_text(json.dumps({"event_id": "bad"}))
    try:
        result = runner.invoke(
            app,
            ["validate", str(contract_path), str(data_path), "--output", "sarif"],
        )
        assert result.exit_code == 1
        assert '"version": "2.1.0"' in result.stdout
    finally:
        data_path.unlink(missing_ok=True)


def test_validate_json_output() -> None:
    contract_path = EXAMPLES_DIR / "customer_events.odcs.yaml"
    result = runner.invoke(app, ["validate", str(contract_path), "--output", "json"])
    assert result.exit_code == 0


def test_validate_invalid_contract(tmp_path: Path) -> None:
    bad = tmp_path / "bad.yaml"
    bad.write_text("not: valid: contract")
    result = runner.invoke(app, ["validate", str(bad), str(bad)])
    assert result.exit_code == 2


def test_diff_json_output() -> None:
    old_path = EXAMPLES_DIR / "customer_events.odcs.yaml"
    result = runner.invoke(app, ["diff", str(old_path), str(old_path), "--output", "json"])
    assert result.exit_code == 0
    assert '"breaking_changes"' in result.stdout


def test_diff_markdown_output() -> None:
    old_path = EXAMPLES_DIR / "customer_events.odcs.yaml"
    result = runner.invoke(app, ["diff", str(old_path), str(old_path), "--output", "markdown"])
    assert result.exit_code == 0
    assert "# Contract Diff" in result.stdout


def test_export_formats(tmp_path: Path) -> None:
    contract_path = EXAMPLES_DIR / "customer_events.odcs.yaml"
    for fmt, outfile in [
        ("odcs", tmp_path / "out.yaml"),
        ("json-schema", tmp_path / "out.json"),
        ("openapi", tmp_path / "openapi.json"),
    ]:
        result = runner.invoke(
            app,
            ["export", str(contract_path), "--to", fmt, "--output", str(outfile)],
        )
        assert result.exit_code == 0, result.stdout
        assert outfile.exists()


def test_export_unsupported_format() -> None:
    contract_path = EXAMPLES_DIR / "customer_events.odcs.yaml"
    result = runner.invoke(app, ["export", str(contract_path), "--to", "xml"])
    assert result.exit_code == 2


def test_generate_unsupported_target() -> None:
    contract_path = EXAMPLES_DIR / "customer_events.odcs.yaml"
    result = runner.invoke(app, ["generate", "sql", str(contract_path)])
    assert result.exit_code == 2


def test_publish_no_registry(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CONTRACT_REGISTRY_URL", raising=False)
    contract_path = EXAMPLES_DIR / "customer_events.odcs.yaml"
    result = runner.invoke(app, ["publish", str(contract_path)])
    assert result.exit_code == 5


def test_publish_success(tmp_path: Path) -> None:
    contract_path = EXAMPLES_DIR / "customer_events.odcs.yaml"
    with patch(
        "contractmodel.cli.app.publish_contract",
        return_value=RegistryPublishResult("id", "1.0.0", "http://r", "201"),
    ):
        result = runner.invoke(
            app,
            ["publish", str(contract_path), "--registry", "http://registry.test"],
        )
    assert result.exit_code == 0
    assert "Published" in result.stdout


def test_export_semantic_formats(tmp_path: Path) -> None:
    contract_path = EXAMPLES_DIR / "customer_events.odcs.yaml"
    pytest.importorskip("rdflib")
    for fmt in ("shacl", "rdf", "owl"):
        result = runner.invoke(
            app,
            ["export", str(contract_path), "--to", fmt, "--output", str(tmp_path / f"out.{fmt}")],
        )
        assert result.exit_code == 0, result.stdout


def test_validate_fail_on_warning() -> None:
    contract_path = EXAMPLES_DIR / "customer_events.odcs.yaml"
    result = runner.invoke(
        app,
        ["validate", str(contract_path), "--mode", "quality_only"],
    )
    assert result.exit_code in (0, 1)


def test_validate_unsupported_format(tmp_path: Path) -> None:
    contract_path = EXAMPLES_DIR / "customer_events.odcs.yaml"
    data = tmp_path / "data.xml"
    data.write_text("<x/>")
    result = runner.invoke(app, ["validate", str(contract_path), str(data), "--format", "xml"])
    assert result.exit_code == 3


def test_diff_invalid_contract(tmp_path: Path) -> None:
    bad = tmp_path / "bad.yaml"
    bad.write_text("invalid")
    good = EXAMPLES_DIR / "customer_events.odcs.yaml"
    result = runner.invoke(app, ["diff", str(good), str(bad)])
    assert result.exit_code == 2


def test_generate_failure(tmp_path: Path) -> None:
    bad = tmp_path / "bad.yaml"
    bad.write_text("not valid")
    result = runner.invoke(app, ["generate", "pydantic", str(bad)])
    assert result.exit_code == 2


def test_export_invalid_contract(tmp_path: Path) -> None:
    bad = tmp_path / "bad.yaml"
    bad.write_text("invalid")
    result = runner.invoke(app, ["export", str(bad), "--to", "markdown"])
    assert result.exit_code == 2


def test_validate_csv_auto_format(tmp_path: Path) -> None:
    pd = pytest.importorskip("pandas")
    contract_path = EXAMPLES_DIR / "customer_events.odcs.yaml"
    csv_path = tmp_path / "data.csv"
    pd.DataFrame(
        [
            {
                "event_id": "550e8400-e29b-41d4-a716-446655440000",
                "customer_id": "C123",
                "event_timestamp": "2026-06-23T12:00:00",
                "event_type": "created",
            }
        ]
    ).to_csv(csv_path, index=False)
    result = runner.invoke(app, ["validate", str(contract_path), str(csv_path)])
    assert result.exit_code == 0


def test_publish_registry_error() -> None:
    from contractmodel.errors import RegistryError

    contract_path = EXAMPLES_DIR / "customer_events.odcs.yaml"
    with patch("contractmodel.cli.app.publish_contract", side_effect=RegistryError("fail")):
        result = runner.invoke(
            app,
            ["publish", str(contract_path), "--registry", "http://registry.test"],
        )
    assert result.exit_code == 5

