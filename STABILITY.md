# API Stability Policy

ContractModel follows [Semantic Versioning](https://semver.org/) for public releases.

See **[ROADMAP.md](ROADMAP.md)** for the 0.2 → 1.0 plan. **0.2.0** ships the
semantic kernel and public integration API. New interchange formats follow the
**0.4** adapter/fidelity framework.

## Tier 1 — Stable (minor releases)

These are intended to remain backward compatible within the 0.x line unless a
serious bug fix requires otherwise. Breaking changes require migration notes.

- `DataContract` loader and validation methods (`load`, `from_yaml`, `from_json`, `from_dict`, `from_odcs`, `validate_*`, `diff`, `to_*` exporters, `save`, `describe`)
- `describe_contract`, `fingerprint_contract`, `canonical_bytes`, `canonical_ccm_dict`
- `ContractDescriptor` and related frozen descriptor types (`ContractIdentity`, `SchemaDescriptor`, `FieldDescriptor`, …)
- `is_contract_model`, `resolve_contract_model`
- `LoadingPolicy`, `DEFAULT_LOADING_POLICY`
- `export_ccm_json_schema` / `load_ccm_json_schema`, `CCM_WIRE_VERSION`
- `export_stability` / `ExportStability` registry
- `ValidationResult`, `ValidationErrorDetail`, `ValidationWarningDetail` field shapes (including `__bool__` and `raise_for_errors()`)
- `ContractDiff`, `BreakingChange`, `NonBreakingChange`, `FieldChange`
- Top-level package exports in `contractmodel.__all__`
- `ValidationMode`, `CompatibilityMode`, `LogicalType`, and `ChangeType` enum member names and values

Call `to_pydantic(mode=...)` once per contract and reuse the returned model class. The same cached model is used for validation at the matching `mode`. Generated models preserve `__contract_id__`, `__contract_version__`, and `__contract_fingerprint__` ClassVars.

`validate_*` methods may merge results from experimental validator plugins when entry points are installed.

### Fingerprint participation

Fingerprints hash identity (`contract_id`, `version`, `name`, `kind`), recursive
schema fields (name, logical_type, required, nullable, constraints, children,
aliases), primary keys/indexes/schema constraints, and extension keys in
`FINGERPRINT_EXTENSION_NAMESPACES` (`apiVersion`, `kind`, `format`). Descriptions,
examples, defaults, and other metadata are excluded.

### Export stability

| Target | Tier |
|--------|------|
| `odcs`, `ccm`, `ccm_json`, `json_schema`, `markdown` | stable |
| `openapi` | provisional |
| `rdf`, `shacl`, `owl` | experimental |

## Tier 2 — Stable with caveats

Compatible within minor releases when possible; may evolve with documentation.

- `CM_*` validation error codes (messages may change with Pydantic upgrades)
- `CanonicalContract`, `ContractField`, and other `contractmodel.core` models (mutable authoring model)
- ODCS import/export fidelity (known lossy fields are reported via `import_warnings` / descriptor fidelity)
- SARIF output structure (version `2.1.0`, rule IDs mirror error codes)

Advanced users may access `DataContract.ccm` and `contractmodel.core`; treat CCM
field additions as non-breaking and renames as breaking.

**Integrators** should use `describe_contract` / `LoadingPolicy` rather than
`contractmodel.validation.limits` or generated `model_fields`.

## Experimental

Not guaranteed stable. Signatures and behavior may change in patch releases.

- Plugin SDK (`contractmodel.plugins`) — entry points are invoked for validate/export/publish when registered
- Registry HTTP client (`contractmodel.registry`) — ContractHub-compatible wire format
- Quality rules (`freshness` is a stub warning; `completeness` is basic)
- Semantic RDF / SHACL / OWL export fidelity
- CLI `publish` and FastAPI `init` scaffold

Plugin and registry trust remain experimental until **0.6**. See [ROADMAP.md](ROADMAP.md).

## Versioning

| Change | Bump |
|--------|------|
| Bug fix, docs, performance | PATCH |
| New optional API, new error codes | MINOR |
| Removed/changed Tier 1 API | MAJOR (1.0.0) |

Supported ranges: ODCS `v3.0.0`–`v3.1.0`; Pydantic `>=2.7,<3`.
