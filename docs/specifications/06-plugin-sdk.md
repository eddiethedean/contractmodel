# Plugin SDK Specification

## Design Goals

- Allow optional integrations without bloating core.
- Use Python entry points.
- Keep plugin contracts small and stable.

Plugin discovery without importing code, allowlists, provenance, and
capability validation remain experimental until ROADMAP **0.6**. See
[ROADMAP.md](../../ROADMAP.md) and [SECURITY.md](../../SECURITY.md).

## Plugin Types

```python
class ValidatorPlugin(Protocol):
    name: str
    version: str
    def validate(self, contract: CanonicalContract, data: Any) -> ValidationResult: ...
```

```python
class ExporterPlugin(Protocol):
    name: str
    version: str
    target: str
    def export(self, contract: CanonicalContract) -> str | bytes | dict[str, Any]: ...
```

```python
class RegistryPlugin(Protocol):
    name: str
    version: str
    def publish(self, contract: CanonicalContract) -> RegistryPublishResult: ...
    def fetch(self, contract_id: str, version: str | None = None) -> CanonicalContract: ...
```

```python
class SemanticPlugin(Protocol):
    name: str
    version: str
    def export_rdf(self, contract: CanonicalContract) -> str: ...
    def export_shacl(self, contract: CanonicalContract) -> str: ...
    def export_owl(self, contract: CanonicalContract) -> str: ...
```

## Entry Points

```toml
[project.entry-points."contractmodel.validators"]
my_validator = "my_package:MyValidator"

[project.entry-points."contractmodel.exporters"]
my_exporter = "my_package:MyExporter"
```

## Plugin Errors

Plugins must raise `ContractPluginError` for expected plugin failures.
