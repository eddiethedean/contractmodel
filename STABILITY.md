# API Stability Policy

ContractModel follows [Semantic Versioning](https://semver.org/) for public releases.

## Tier 1 — Stable (minor releases)

These are intended to remain backward compatible within the 0.x line unless a serious bug fix requires otherwise. Breaking changes are reserved for **0.2.0+** with migration notes.

- `DataContract` loader and validation methods (`load`, `from_yaml`, `from_json`, `from_dict`, `from_odcs`, `validate_*`, `diff`, `to_*` exporters, `save`)
- `ValidationResult`, `ValidationErrorDetail`, `ValidationWarningDetail` field shapes (including `__bool__` and `raise_for_errors()`)
- `ContractDiff`, `BreakingChange`, `NonBreakingChange`, `FieldChange`
- Top-level package exports in `contractmodel.__all__`
- `ValidationMode`, `CompatibilityMode`, `LogicalType`, and `ChangeType` enum member names and values

Call `to_pydantic(mode=...)` once per contract and reuse the returned model class. The same cached model is used for validation at the matching `mode`.

`validate_*` methods may merge results from experimental validator plugins when entry points are installed.

## Tier 2 — Stable with caveats

Compatible within minor releases when possible; may evolve with documentation.

- `CM_*` validation error codes (messages may change with Pydantic upgrades)
- `CanonicalContract`, `ContractField`, and other `contractmodel.core` models
- ODCS import/export fidelity (known lossy fields are reported via `import_warnings`)
- SARIF output structure (version `2.1.0`, rule IDs mirror error codes)

Advanced users may access `DataContract.ccm` and `contractmodel.core`; treat CCM field additions as non-breaking and renames as breaking.

## Experimental (0.1.x)

Not guaranteed stable. Signatures and behavior may change in patch releases.

- Plugin SDK (`contractmodel.plugins`) — entry points are invoked for validate/export/publish when registered
- Registry HTTP client (`contractmodel.registry`) — ContractHub-compatible wire format
- Quality rules (`freshness` is a stub warning; `completeness` is basic)
- Semantic RDF / SHACL / OWL export fidelity
- CLI `publish` and FastAPI `init` scaffold

## Versioning

| Change | Bump |
|--------|------|
| Bug fix, docs, performance | PATCH (0.1.x) |
| New optional API, new error codes | MINOR (0.2.0) |
| Removed/changed Tier 1 API | MAJOR (1.0.0) |

Pre-1.0 patch releases (including 0.1.2) may add documented helpers such as `load`, `save`, and validation limits without a minor bump.
