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
from contractmodel.errors import OptionalDependencyError

app = typer.Typer(help="ContractModel — Python-native data contracts")


class OutputFormat(str, Enum):
    TEXT = "text"
    JSON = "json"
    MARKDOWN = "markdown"


@app.command()
def init(
    path: Path = typer.Argument(Path("contract.yaml")),
    template: str = typer.Option("ccm", "--template", help="Template: ccm or odcs"),
) -> None:
    """Initialize a new contract file."""
    if path.exists():
        typer.echo(f"File already exists: {path}", err=True)
        raise typer.Exit(code=3)

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

    if output == OutputFormat.JSON:
        typer.echo(result.model_dump_json(indent=2))
    else:
        if result.success:
            typer.echo("Validation passed.")
        else:
            for error in result.errors:
                location = f" (row {error.row})" if error.row is not None else ""
                typer.echo(f"[{error.code}] {error.field}{location}: {error.message}", err=True)

    raise typer.Exit(code=0 if result.success else 1)


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
    to: str = typer.Option(..., "--to", help="Export format: odcs, markdown, json-schema"),
    output: Path | None = typer.Option(None, "--output", help="Output file path"),
) -> None:
    """Export a contract to another format."""
    try:
        contract = DataContract.from_yaml(contract_path)
    except Exception as exc:
        typer.echo(f"Invalid contract: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    if to == "odcs":
        content = yaml.safe_dump(contract.to_odcs(), sort_keys=False)
    elif to == "markdown":
        content = contract.to_markdown()
    elif to == "json-schema":
        content = json.dumps(contract.to_json_schema(), indent=2)
    else:
        typer.echo(f"Unsupported export format: {to}", err=True)
        raise typer.Exit(code=2)

    if output:
        output.write_text(content)
        typer.echo(f"Wrote {output}")
    else:
        typer.echo(content)


@app.command()
def doctor() -> None:
    """Check environment and optional dependencies."""
    typer.echo(f"Python: {sys.version.split()[0]}")
    for extra, module in [
        ("pandas", "pandas"),
        ("polars", "polars"),
        ("parquet", "pyarrow"),
        ("cli", "typer"),
        ("semantic", "rdflib"),
    ]:
        try:
            __import__(module)
            typer.echo(f"  {extra}: installed")
        except ImportError:
            typer.echo(f"  {extra}: not installed")


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
        return contract.validate_json(data_path.read_text(), mode=mode)
    msg = f"Unsupported data format: {resolved_format}"
    raise ValueError(msg)


def _render_pydantic_model_source(model: type[BaseModel]) -> str:
    """Render a minimal importable Python module for a generated model."""
    lines = [
        "from contractmodel import ContractModel",
        "from pydantic import Field",
        "",
        f"class {model.__name__}(ContractModel):",
    ]
    if not model.model_fields:
        lines.append("    pass")
    else:
        for name, field in model.model_fields.items():
            annotation = getattr(field.annotation, "__name__", str(field.annotation))
            if field.is_required():
                lines.append(f"    {name}: {annotation}")
            else:
                lines.append(f"    {name}: {annotation} | None = None")
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    app()
