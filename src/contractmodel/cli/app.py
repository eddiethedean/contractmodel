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
from contractmodel.core.types import CompatibilityMode, ValidationMode
from contractmodel.errors import ContractPluginError, OptionalDependencyError, RegistryError
from contractmodel.plugins.runtime import list_plugins, run_exporter_plugin, run_registry_publish
from contractmodel.registry.client import get_registry_url, publish_contract
from contractmodel.validation.sarif import validation_result_to_sarif

app = typer.Typer(help="ContractModel — Python-native data contracts")


class OutputFormat(str, Enum):
    TEXT = "text"
    JSON = "json"
    MARKDOWN = "markdown"
    SARIF = "sarif"


_VALID_INIT_TEMPLATES = frozenset({"ccm", "odcs", "fastapi"})


@app.command()
def init(
    path: Path = typer.Argument(Path("contract.yaml")),
    template: str = typer.Option("ccm", "--template", help="Template: ccm, odcs, or fastapi"),
) -> None:
    """Initialize a new contract file."""
    if template not in _VALID_INIT_TEMPLATES:
        typer.echo(
            f"Unknown template: {template!r}. "
            f"Choose from: {', '.join(sorted(_VALID_INIT_TEMPLATES))}",
            err=True,
        )
        raise typer.Exit(code=2)

    if path.exists():
        typer.echo(f"File already exists: {path}", err=True)
        raise typer.Exit(code=3)

    if template == "fastapi":
        app_dir = path if path.suffix == "" else path.parent / path.stem
        app_dir.mkdir(parents=True, exist_ok=True)
        (app_dir / "main.py").write_text(
            "# Security: add authentication and CORS before exposing this API publicly.\n"
            "from fastapi import FastAPI\n\nfrom contractmodel import DataContract\n\n"
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
            "apiVersion": "v3.1.0",
            "kind": "DataContract",
            "id": "my-contract",
            "name": "My Contract",
            "version": "1.0.0",
            "status": "draft",
            "description": {"purpose": "A new data contract."},
            "schema": [
                {
                    "name": "my_contract",
                    "logicalType": "object",
                    "properties": [
                        {"name": "id", "logicalType": "string", "required": True},
                    ],
                }
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
        contract = DataContract.load(contract_path)
    except Exception as exc:
        typer.echo(f"Invalid contract: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    if data_path is None:
        typer.echo("Contract is valid.")
        raise typer.Exit(code=0)

    try:
        result = contract.validate(data_path, format=format, mode=mode)
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
    odcs: bool = typer.Option(
        False,
        "--odcs",
        help="Use pyodcs ODCS-native compatibility instead of CCM diff",
    ),
) -> None:
    """Diff two contract versions."""
    try:
        old_contract = DataContract.load(old_path)
        new_contract = DataContract.load(new_path)
    except Exception as exc:
        typer.echo(f"Invalid contract: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    if odcs:
        report = old_contract.diff_odcs(new_contract)
        if output == OutputFormat.JSON:
            typer.echo(json.dumps(report, indent=2))
        else:
            breaking = bool(report.get("hasBreaking"))
            typer.echo(f"Breaking: {breaking}")
            for change in report.get("changes", []):
                if isinstance(change, dict):
                    kind = change.get("kind", "change")
                    message = change.get("message", "")
                    typer.echo(f"[{kind}] {message}")
        raise typer.Exit(code=1 if report.get("hasBreaking") else 0)

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
        if result.added_fields:
            typer.echo(f"Added: {', '.join(result.added_fields)}")
        if result.removed_fields:
            typer.echo(f"Removed: {', '.join(result.removed_fields)}")
        if result.changed_fields:
            changed = ", ".join(
                f"{change.field} ({change.change_type.value})" for change in result.changed_fields
            )
            typer.echo(f"Changed: {changed}")
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
        contract = DataContract.load(contract_path)
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
        contract = DataContract.load(contract_path)
    except Exception as exc:
        typer.echo(f"Invalid contract: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    try:
        plugin_content = run_exporter_plugin(contract.ccm, to)
        content: str | bytes
        if plugin_content is not None:
            if isinstance(plugin_content, bytes):
                content = plugin_content
            elif isinstance(plugin_content, (dict, list)):
                content = json.dumps(plugin_content, indent=2)
            else:
                content = str(plugin_content)
        elif to == "odcs":
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
    except ContractPluginError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=4) from exc
    except Exception as exc:
        typer.echo(f"Export failed: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    if output:
        if isinstance(content, bytes):
            output.write_bytes(content)
        else:
            output.write_text(content)
        typer.echo(f"Wrote {output}")
    else:
        if isinstance(content, bytes):
            typer.echo(content.decode("utf-8", errors="replace"))
        else:
            typer.echo(content)


@app.command()
def publish(
    contract_path: Path = typer.Argument(..., help="Path to contract file"),
    registry: str | None = typer.Option(None, "--registry", help="Registry URL"),
) -> None:
    """Publish a contract to a registry."""
    try:
        contract = DataContract.load(contract_path)
        registry_url = registry or get_registry_url()
        if not registry_url:
            typer.echo("Registry URL not configured", err=True)
            raise typer.Exit(code=5)
        plugin_result = run_registry_publish(contract.ccm, registry_url)
        if plugin_result is not None:
            typer.echo(f"Published via registry plugin to {registry_url}")
        else:
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
    import pyodcs

    import contractmodel

    typer.echo(f"Python: {sys.version.split()[0]}")
    typer.echo(f"contractmodel: {contractmodel.__version__}")
    typer.echo(f"pyodcs: {pyodcs.__version__} (ODCS {pyodcs.UPSTREAM_SPEC_VERSION})")
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


def _render_pydantic_model_source(model: type[BaseModel]) -> str:
    """Render an importable Python module for a generated model."""
    from typing import get_args, get_origin

    nested_models: dict[str, type[BaseModel]] = {}

    def _collect_nested(annotation_obj: object) -> None:
        origin = get_origin(annotation_obj)
        if origin is list or origin is dict:
            for arg in get_args(annotation_obj):
                _collect_nested(arg)
            return
        if isinstance(annotation_obj, type) and issubclass(annotation_obj, BaseModel):
            if annotation_obj is model or annotation_obj.__name__ in nested_models:
                return
            nested_models[annotation_obj.__name__] = annotation_obj
            for nested_field in annotation_obj.model_fields.values():
                _collect_nested(nested_field.annotation)

    for field in model.model_fields.values():
        _collect_nested(field.annotation)

    lines = [
        "from __future__ import annotations",
        "",
        "from typing import ClassVar",
        "",
        "from contractmodel import ContractModel",
        "from pydantic import Field",
        "",
    ]

    def _annotation_name(annotation_obj: object) -> str:
        origin = get_origin(annotation_obj)
        if origin is list:
            args = get_args(annotation_obj)
            inner = _annotation_name(args[0]) if args else "object"
            return f"list[{inner}]"
        if origin is dict:
            args = get_args(annotation_obj)
            key = _annotation_name(args[0]) if args else "str"
            value = _annotation_name(args[1]) if len(args) > 1 else "object"
            return f"dict[{key}, {value}]"
        if isinstance(annotation_obj, type) and issubclass(annotation_obj, BaseModel):
            return annotation_obj.__name__
        name = getattr(annotation_obj, "__name__", None)
        if isinstance(name, str) and name:
            return name
        return str(annotation_obj).replace("typing.", "")

    def _render_class(cls: type[BaseModel], *, base: str) -> list[str]:
        class_lines = [f"class {cls.__name__}({base}):"]
        identity_attrs = [
            ("__contract_id__", getattr(cls, "__contract_id__", None)),
            ("__contract_version__", getattr(cls, "__contract_version__", None)),
            ("__contract_name__", getattr(cls, "__contract_name__", None)),
            ("__contract_fingerprint__", getattr(cls, "__contract_fingerprint__", None)),
            ("__ccm_wire_version__", getattr(cls, "__ccm_wire_version__", None)),
            ("__contract_kind__", getattr(cls, "__contract_kind__", None)),
            ("__source_format__", getattr(cls, "__source_format__", None)),
            ("__source_version__", getattr(cls, "__source_version__", None)),
        ]
        has_identity = False
        for attr_name, attr_value in identity_attrs:
            if attr_value is not None:
                class_lines.append(f"    {attr_name}: ClassVar[str | None] = {attr_value!r}")
                has_identity = True
        if has_identity:
            class_lines.append("")

        if not cls.model_fields:
            if not has_identity:
                class_lines.append("    pass")
        else:
            for name, field in cls.model_fields.items():
                annotation = _annotation_name(field.annotation)
                if field.is_required():
                    class_lines.append(f"    {name}: {annotation}")
                else:
                    default = field.default if field.default is not None else None
                    class_lines.append(f"    {name}: {annotation} | None = {default!r}")
        class_lines.append("")
        return class_lines

    for nested in nested_models.values():
        lines.extend(_render_class(nested, base="ContractModel"))
        lines.append("")

    lines.extend(_render_class(model, base="ContractModel"))
    return "\n".join(lines)


if __name__ == "__main__":
    app()
