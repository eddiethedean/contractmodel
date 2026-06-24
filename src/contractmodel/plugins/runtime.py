"""Plugin runtime dispatch."""

from __future__ import annotations

from typing import Any, cast

from contractmodel.core.ccm import CanonicalContract
from contractmodel.core.result import ValidationResult
from contractmodel.errors import ContractPluginError
from contractmodel.plugins.manager import discover_entry_points, list_plugin_names


def list_plugins() -> dict[str, list[str]]:
    """List plugin entry point names without loading plugin modules."""
    return {
        "validators": list_plugin_names("contractmodel.validators"),
        "exporters": list_plugin_names("contractmodel.exporters"),
        "registries": list_plugin_names("contractmodel.registries"),
    }


def run_validator_plugins(
    contract: CanonicalContract,
    data: Any,
    base: ValidationResult,
) -> ValidationResult:
    """Run installed validator plugins and merge results into base."""
    plugins = discover_entry_points("contractmodel.validators")
    if not plugins:
        return base

    errors = list(base.errors)
    warnings = list(base.warnings)
    success = base.success

    for name, plugin in plugins.items():
        try:
            result = plugin.validate(contract, data)
        except Exception as exc:
            raise ContractPluginError(f"Validator plugin '{name}' failed") from exc
        if not isinstance(result, ValidationResult):
            msg = f"Validator plugin '{name}' must return ValidationResult"
            raise ContractPluginError(msg)
        errors.extend(result.errors)
        warnings.extend(result.warnings)
        success = success and result.success

    return ValidationResult(
        success=success and len(errors) == 0,
        error_count=len(errors),
        warning_count=len(warnings),
        errors=errors,
        warnings=warnings,
        metrics=dict(base.metrics),
    )


def run_exporter_plugin(
    contract: CanonicalContract,
    target: str,
) -> str | bytes | dict[str, Any] | None:
    """Return export content from a matching exporter plugin, or None."""
    plugins = discover_entry_points("contractmodel.exporters")
    for name, plugin in plugins.items():
        plugin_target = getattr(plugin, "target", None)
        if plugin_target != target:
            continue
        try:
            exported = plugin.export(contract)
        except Exception as exc:
            raise ContractPluginError(f"Exporter plugin '{name}' failed") from exc
        if exported is None:
            msg = f"Exporter plugin '{name}' returned no content"
            raise ContractPluginError(msg)
        return cast(str | bytes | dict[str, Any], exported)
    return None


def run_registry_publish(contract: CanonicalContract, registry_url: str) -> Any | None:
    """Publish via a registry plugin when one is installed, else None."""
    plugins = discover_entry_points("contractmodel.registries")
    if not plugins:
        return None
    name, plugin = next(iter(plugins.items()))
    try:
        return plugin.publish(contract, registry_url)
    except TypeError:
        return plugin.publish(contract)
    except Exception as exc:
        raise ContractPluginError(f"Registry plugin '{name}' failed") from exc
