"""ContractModel CLI."""

from __future__ import annotations

import json
import sys
from enum import Enum
from pathlib import Path
from typing import Any

import typer
import yaml
from pydantic import BaseModel

from contractmodel.contract import DataContract
from contractmodel.core.result import ValidationResult
from contractmodel.core.types import CompatibilityMode, ValidationMode
from contractmodel.errors import ContractPluginError, OptionalDependencyError, RegistryError
from contractmodel.plugins.manager import list_plugins
from contractmodel.registry.client import get_registry_url, publish_contract
from contractmodel.validation.sarif import validation_result_to_sarif

app = typer.Typer(help="ContractModel — Python-native data contracts")


class OutputFormat(str, Enum):
    TEXT = "text"
    JSON = "json"
    MARKDOWN = "markdown"
    SARIF = "sarif"


@app.command()
def init(
    path: Path = typer.Argument(Path("contract.yaml")),
    template: str = typer.Option("ccm", "--template", help="Template: ccm, odcs, or fastapi"),
) -> None:
    """Initialize a new contract file."""
    if path.exists():
        typer.echo(f"File already exists: {path}", err=True)
        raise typer.Exit(code=3)

    if template == "fastapi":
        app_dir = path if path.suffix == "" else path.parent / path.stem
        app_dir.mkdir(parents=True, exist_ok=True)
        (app_dir / "main.py").write_text(
            'from fastapi import FastAPI\n\nfrom contractmodel import DataContract\n\n'
            'app = FastAPI()\ncontract = DataContract.from_yaml("contract.yaml")\n\n\n'
            '@app.get("/schema")\ndef schema():\n    return contract.to_json_schema()\n'
        )
        contract_path = app_dir / "contract.yaml"
        contract_content: dict[str, Any] = {
            "contract_id": "my-contract",
            "name": "My Contract",
            "version": "1.0.0",
            "schema": {"fields": [{"name": "id", "logical_type": "string", "required": True}]},
        }
        with contract_path.open("w") as f:
            yaml.safe_dump(contract_content, f, sort_keys=False)
        typer.echo(f"Created FastAPI scaffold in {app_dir}")
        return

    content: dict[str, Any]
    if template == "odcs":
        content = {
            "apiVersion": "v3.0.0",
            "kind": "DataContract",
            "id": "my-contract",
            "name": "My Contract",
            "version": "1.0.0",
            "description": "A new data contract.",
            "schema": [
                {"name": "id", "logicalType": "string", "required": True},
            ],
        }
    else:
        content = {
            "contract_id": "my-contract",
            "name": "My Contract",
            "version": "1.0.0",
            "schema": {
                "fields": [
                    {"name": "id", "logical_type": "string", "required": True},
                ]
            },
        }

    with path.open("w") as f:
        yaml.safe_dump(content, f, sort_keys=False)
    typer.echo(f"Created {path}")


@app.command()
def validate(
    contract_path: Path = typer.Argument(..., help="Path to contract file"),
    data_path: Path | None = typer.Argument(None, help="Path to data file"),
    format: str = typer.Option("auto", "--format", help="Data format: auto, csv, json, parquet"),
    mode: ValidationMode = typer.Option(ValidationMode.STRICT, "--mode"),
    output: OutputFormat = typer.Option(OutputFormat.TEXT, "--output"),
    fail_on_warning: bool = typer.Option(False, "--fail-on-warning"),
) -> None:
    """Validate data against a contract."""
    try:
        contract = DataContract.from_yaml(contract_path)
    except Exception as exc:
        typer.echo(f"Invalid contract: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    if data_path is None:
        typer.echo("Contract is valid.")
        raise typer.Exit(code=0)

    try:
        result = _validate_data(contract, data_path, format=format, mode=mode)
    except OptionalDependencyError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=3) from exc
    except Exception as exc:
        typer.echo(f"Validation error: {exc}", err=True)
        raise typer.Exit(code=3) from exc

    exit_code = 0 if result.success else 1
    if fail_on_warning and result.warning_count > 0:
        exit_code = 1

    if output == OutputFormat.JSON:
        typer.echo(result.model_dump_json(indent=2))
    elif output == OutputFormat.SARIF:
        typer.echo(json.dumps(validation_result_to_sarif(result), indent=2))
    else:
        if result.success and result.warning_count == 0:
            typer.echo("Validation passed.")
        else:
            for error in result.errors:
                location = f" (row {error.row})" if error.row is not None else ""
                typer.echo(f"[{error.code}] {error.field}{location}: {error.message}", err=True)
            for warning in result.warnings:
                typer.echo(f"[{warning.code}] {warning.message}", err=True)

    raise typer.Exit(code=exit_code)


@app.command()
def diff(
    old_path: Path = typer.Argument(..., help="Old contract path"),
    new_path: Path = typer.Argument(..., help="New contract path"),
    mode: CompatibilityMode = typer.Option(CompatibilityMode.BACKWARD, "--mode"),
    output: OutputFormat = typer.Option(OutputFormat.TEXT, "--output"),
) -> None:
    """Diff two contract versions."""
    try:
        old_contract = DataContract.from_yaml(old_path)
        new_contract = DataContract.from_yaml(new_path)
    except Exception as exc:
        typer.echo(f"Invalid contract: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    result = old_contract.diff(new_contract, mode=mode)

    if output == OutputFormat.JSON:
        typer.echo(result.model_dump_json(indent=2))
    elif output == OutputFormat.MARKDOWN:
        lines = [
            f"# Contract Diff: {result.source_version} -> {result.target_version}",
            "",
            f"**Breaking**: {result.is_breaking}",
            "",
            "## Added Fields",
            *[f"- {name}" for name in result.added_fields],
            "",
            "## Removed Fields",
            *[f"- {name}" for name in result.removed_fields],
            "",
            "## Breaking Changes",
            *[f"- {change.message}" for change in result.breaking_changes],
            "",
            "## Non-Breaking Changes",
            *[f"- {change.message}" for change in result.non_breaking_changes],
        ]
        typer.echo("\n".join(lines))
    else:
        typer.echo(f"Diff {result.source_version} -> {result.target_version}")
        typer.echo(f"Breaking: {result.is_breaking}")
        for breaking_change in result.breaking_changes:
            typer.echo(f"  BREAKING: {breaking_change.message}")
        for non_breaking_change in result.non_breaking_changes:
            typer.echo(f"  OK: {non_breaking_change.message}")

    raise typer.Exit(code=1 if result.is_breaking else 0)


@app.command("generate")
def generate(
    target: str = typer.Argument(..., help="Generation target: pydantic"),
    contract_path: Path = typer.Argument(..., help="Path to contract file"),
    output: Path = typer.Option(Path("models.py"), "--output", help="Output file path"),
    class_name: str | None = typer.Option(None, "--class-name"),
) -> None:
    """Generate artifacts from a contract."""
    if target != "pydantic":
        typer.echo(f"Unsupported generation target: {target}", err=True)
        raise typer.Exit(code=2)

    try:
        contract = DataContract.from_yaml(contract_path)
        model = contract.to_pydantic(class_name=class_name)
    except Exception as exc:
        typer.echo(f"Generation failed: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    source = _render_pydantic_model_source(model)
    output.write_text(source)
    typer.echo(f"Wrote {output}")


@app.command()
def export(
    contract_path: Path = typer.Argument(..., help="Path to contract file"),
    to: str = typer.Option(..., "--to", help="Export format"),
    output: Path | None = typer.Option(None, "--output", help="Output file path"),
) -> None:
    """Export a contract to another format."""
    try:
        contract = DataContract.from_yaml(contract_path)
    except Exception as exc:
        typer.echo(f"Invalid contract: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    try:
        if to == "odcs":
            content = yaml.safe_dump(contract.to_odcs(), sort_keys=False)
        elif to == "markdown":
            content = contract.to_markdown()
        elif to == "json-schema":
            content = json.dumps(contract.to_json_schema(), indent=2)
        elif to == "openapi":
            content = json.dumps(contract.to_openapi(), indent=2)
        elif to == "shacl":
            content = contract.to_shacl()
        elif to == "rdf":
            content = contract.to_rdf()
        elif to == "owl":
            content = contract.to_owl()
        else:
            typer.echo(f"Unsupported export format: {to}", err=True)
            raise typer.Exit(code=2)
    except OptionalDependencyError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=3) from exc

    if output:
        output.write_text(content)
        typer.echo(f"Wrote {output}")
    else:
        typer.echo(content)


@app.command()
def publish(
    contract_path: Path = typer.Argument(..., help="Path to contract file"),
    registry: str | None = typer.Option(None, "--registry", help="Registry URL"),
) -> None:
    """Publish a contract to a registry."""
    try:
        contract = DataContract.from_yaml(contract_path)
        registry_url = registry or get_registry_url()
        if not registry_url:
            typer.echo("Registry URL not configured", err=True)
            raise typer.Exit(code=5)
        result = publish_contract(contract.ccm, registry_url)
        typer.echo(f"Published {result.contract_id}@{result.version} to {result.registry_url}")
    except typer.Exit:
        raise
    except RegistryError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=5) from exc
    except ContractPluginError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=4) from exc
    except Exception as exc:
        typer.echo(f"Publish failed: {exc}", err=True)
        raise typer.Exit(code=2) from exc


@app.command()
def doctor() -> None:
    """Check environment and optional dependencies."""
    typer.echo(f"Python: {sys.version.split()[0]}")
    for extra, module in [
        ("pandas", "pandas"),
        ("polars", "polars"),
        ("parquet", "pyarrow"),
        ("semantic", "rdflib"),
    ]:
        try:
            __import__(module)
            typer.echo(f"  {extra}: installed")
        except ImportError:
            typer.echo(f"  {extra}: not installed")

    registry_url = get_registry_url()
    typer.echo(f"  registry: {registry_url or 'not configured'}")

    plugins = list_plugins()
    for group, names in plugins.items():
        if names:
            typer.echo(f"  plugins.{group}: {', '.join(names)}")
        else:
            typer.echo(f"  plugins.{group}: none")


def _validate_data(
    contract: DataContract,
    data_path: Path,
    *,
    format: str,
    mode: ValidationMode,
) -> ValidationResult:
    suffix = data_path.suffix.lower()
    resolved_format = format
    if resolved_format == "auto":
        if suffix == ".csv":
            resolved_format = "csv"
        elif suffix == ".parquet":
            resolved_format = "parquet"
        else:
            resolved_format = "json"

    if resolved_format == "csv":
        return contract.validate_csv(data_path, mode=mode)
    if resolved_format == "parquet":
        return contract.validate_parquet(data_path, mode=mode)
    if resolved_format == "json":
        return contract.validate_json(data_path.read_text(encoding="utf-8"), mode=mode)
    msg = f"Unsupported data format: {resolved_format}"
    raise ValueError(msg)


def _render_pydantic_model_source(model: type[BaseModel]) -> str:
    """Render an importable Python module for a generated model."""
    lines = [
        "from __future__ import annotations",
        "",
        "from contractmodel import ContractModel",
        "from pydantic import Field",
        "",
        f"class {model.__name__}(ContractModel):",
    ]
    if not model.model_fields:
        lines.append("    pass")
    else:
        for name, field in model.model_fields.items():
            annotation = getattr(field.annotation, "__name__", None) or str(field.annotation)
            annotation = annotation.replace("typing.", "")
            if field.is_required():
                lines.append(f"    {name}: {annotation}")
            else:
                default = field.default if field.default is not None else None
                lines.append(f"    {name}: {annotation} | None = {default!r}")
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    app()
