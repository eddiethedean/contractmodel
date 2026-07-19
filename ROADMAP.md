# ContractModel Roadmap

Proposed path from **0.2.0** to a stable **1.0** data-contract foundation, and its
integration with ETLantic.

Detailed design notes live in
[`docs/CONTRACTMODEL_UPGRADE_PLAN.md`](docs/CONTRACTMODEL_UPGRADE_PLAN.md).
Format-specific status lives in
[`docs/roadmap/03-data-contract-formats.md`](docs/roadmap/03-data-contract-formats.md).

## Product outcome

ContractModel should be the best Python-native way to turn a data contract into
an operational, portable, inspectable interface:

```text
ODCS or Python authoring
          ↓
versioned canonical contract semantics
          ↓
introspection • validation • compatibility • fidelity evidence
          ↓
pipelines, applications, CI, registries, and engine adapters
```

| Layer | Owns |
|-------|------|
| **ContractModel** | What a valid data contract means |
| **ETLantic** | Where and when that contract is applied |
| **Execution plugins** | How a required check runs on a backend |

Dependency is strictly one-way: ContractModel never imports ETLantic, DTCS,
DPCS, pipeline plans, orchestrators, or dataframe execution plugins.

## Status today (0.2.0)

Phases 0–11 from the original bootstrap roadmap are complete. **0.2** ships the
semantic kernel and public integration API:

- `DataContract` facade over a Canonical Contract Model (CCM)
- Wire schema `contractmodel.ccm/1`, immutable descriptors, and stable fingerprints
- Recognition helpers and public `LoadingPolicy`
- ODCS and Pydantic round trips with identity preservation
- Structured record, JSON, CSV, Parquet, Pandas, and Polars validation
- Compatibility modes and structured contract diffs
- JSON Schema, OpenAPI, Markdown, RDF, SHACL, and OWL exports
- CLI, examples, SARIF, error codes, and API stability tiers

Remaining 0.3+ work focuses on bounded validation, adapter fidelity, compatibility
depth, trust, and conformance.

## Prioritization

Prefer semantic depth over adapter count:

1. Canonical semantics and identity
2. Bounded validation and evidence
3. Compatibility and fidelity
4. Trust and conformance
5. Developer experience
6. Additional formats and registries

A new adapter should not outrank a missing guarantee in the canonical model it
targets.

## Release plan

### 0.2 — Semantic kernel and integration API

**Status: implemented in 0.2.0**

**Deliver**

- Publish `contractmodel.ccm/1` and its complete JSON Schema
- Immutable descriptor, schema, field, constraint, identity, provenance,
  fidelity, and fingerprint values
- Canonical JSON and exact fingerprint participation rules
- Preserve identity/version/provenance across ODCS → Pydantic → CCM round trips
- Public recognition and annotation-resolution helpers
- Public bounded loading policy
- Extension namespaces, JSON-value constraints, and size budgets
- Supported ODCS and Pydantic ranges (cap Pydantic below v3)
- Classify every export as stable, provisional, experimental, or private

**Exit gate:** ETLantic can implement its data-contract analysis boundary using
only documented top-level ContractModel APIs.

### 0.3 — Bounded validation protocol

**Deliver**

- Versioned immutable validation specification and result schemas
- Deterministic diagnostic budgets; redact values by default
- Iterator/batch validation without unconditional materialization
- Cancellation, timeout, partial-result, and cleanup semantics
- Exact / approximate / unsupported / skipped / failed check outcomes
- Invalid-row separation only through runtime handles
- Reference engine separate from optional engine adapters
- Validation-engine conformance suite

### 0.4 — Adapter and fidelity framework

**Deliver**

- Versioned adapter protocol and static manifest
- Format/version ranges, capabilities, fidelity, and dependency tier
- Bounded contexts and structured fidelity results
- Golden and property-based round-trip suites
- Graduate ODCS under the protocol, then JSON Schema
- Prioritize further formats by semantic coverage and user value, not count

New interchange formats (Avro, Protobuf, Parquet schema, dbt, lakehouse, and
so on) land **after** this framework is in place. See the
[format catalog](docs/roadmap/03-data-contract-formats.md).

### 0.5 — Compatibility and evolution

**Deliver**

- Compatibility policy versioned independently from CCM
- Identical / compatible / conditional / breaking / unknown outcomes
- Nested, rename, default, required/nullable, enum, numeric, temporal,
  composite, constraint, key, index, and semantic changes
- Producer, consumer, backward, forward, and full compatibility
- Deterministic migration guidance and machine-readable actions
- CCM/result schema migration functions and historical fixtures

### 0.6 — Trust, plugins, and registries

**Deliver**

- Split plugin discovery, evaluation, authorization, and loading
- Static manifest inspection without importing entry points
- Protocol versions, allowlists, provenance/digests, and conflict detection
- Adversarial conformance and an external reference plugin
- Registry scheme/host/address, redirect, TLS, timeout, and private-target policy
- Credentials bound to approved origins; digest/signature checks
- Security events without credentials or source samples

These surfaces remain experimental until they fail closed.

### 0.7 — Developer experience and CLI

**Deliver**

- CLI workflows: `init`, `inspect`, `validate`, `diff`, `convert`, `export`,
  `doctor`, and optional `registry`
- Standardized human / JSON / SARIF diagnostics and exit codes
- Consistent dry-run, color, quiet, verbose, and non-interactive behavior
- Targets and overwrite policy for every mutation
- `doctor` inspects manifests and safety without loading plugins
- Deterministic importable Python generation (type-checkable)
- Guides for users, adapter/engine authors, and integrators

**Exit gate:** The CLI is a projection of the public library API, not parallel
semantics.

### 0.8 — Performance and conformance

**Deliver**

- Time/memory budgets for load, normalize, generate, validate, diff, and export
- Benchmarks for nested/wide contracts and representative data sizes
- Hypothesis properties and malformed/deep/recursive fuzz corpora
- Linux, macOS, Windows, and every supported Python line
- Minimal core and each optional extra from isolated wheels
- ETLantic against minimum and latest ContractModel versions
- Conformance packages for external engines/adapters

### 0.9 — 1.0 release candidate

- Freeze API, CCM, descriptor, validation, compatibility, diagnostic, fidelity,
  adapter, and plugin snapshots
- Rehearse upgrades from every supported 0.x artifact
- Publish removals and migrations for deprecated 0.1 APIs
- Complete security control-to-test traceability
- Generate SBOMs and signed provenance; use trusted publishing
- Run source, sdist, and wheel acceptance on all supported platforms

### 1.0 — Stable data-contract foundation

Ship only when:

- Canonical and public result schemas are versioned and stable
- Canonical bytes and fingerprints are deterministic and verified
- Python/ODCS round trips publish complete fidelity evidence
- Validation is bounded, redactable, cancellable, and engine-conformant
- Compatibility covers every stable logical type and constraint
- Plugin and registry trust boundaries fail closed
- Supported adapters pass round-trip/fidelity conformance
- CLI and library expose the same semantics
- Minimal and optional installations pass isolated wheels
- ETLantic depends only on stable public APIs
- ContractModel has no ETLantic or pipeline-specific dependency

## Required public integration API (0.2+)

Illustrative names; required capabilities:

| Capability | Purpose |
|------------|---------|
| **Recognition** | `is_contract_model` / `resolve_contract_model` |
| **Descriptor** | Immutable identity, version, schema, fingerprint, provenance, fidelity |
| **Generated-model identity** | Preserve ID/version/fingerprint across Pydantic generation |
| **Compatibility report** | Structured findings; no message parsing |
| **Validation spec/result** | Budgets, redaction, cancellation, engine evidence |
| **Safe loading policy** | Public policy replaces private `validation.limits` imports |
| **Adapter fidelity** | Exact / normalized / extended / lossy / unsupported / rejected |

## ETLantic adoption

1. Shared fixtures covering nested fields, aliases, constraints, nullability,
   decimals, temporals, enums, arrays, maps, and extensions
2. Dual-version acceptance against 0.1.2 and 0.2 prereleases
3. Replace duplicated introspection with public helpers and descriptors
4. Pin a bounded range (for example `contractmodel>=0.2,<0.3`) after validation
5. Joint 1.0 interoperability rehearsal (identity, validation parity, evidence)

The projects do not need lockstep versions or release schedules.

## Success measures

- ETLantic imports no private ContractModel modules
- One descriptor replaces repeated Pydantic introspection
- Equivalent contracts have stable cross-process fingerprints
- Validation results are source-row-free by default
- Adapter losses are machine-readable and path-specific
- Third-party validators/adapters pass public conformance
- Unsafe plugins and registry destinations fail before effects
- Core-only import remains lightweight
- Scale and compatibility are measured rather than implied

## Related documents

| Document | Role |
|----------|------|
| [Upgrade plan](docs/CONTRACTMODEL_UPGRADE_PLAN.md) | Full findings, ownership boundary, acceptance criteria |
| [Format catalog](docs/roadmap/03-data-contract-formats.md) | Per-format status and priority |
| [Historical phases 0–11](docs/roadmap/01-implementation-roadmap.md) | Completed 0.1.x bootstrap work |
| [GitHub epics](docs/roadmap/02-github-epics-and-issues.md) | Issue tracking skeleton |
| [STABILITY.md](STABILITY.md) | API stability tiers |
| [CHANGELOG.md](CHANGELOG.md) | Released changes |
