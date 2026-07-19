# ContractModel documentation

Welcome to the ContractModel docs. Start here if you cloned the repo or want depth beyond the [project README](https://github.com/eddiethedean/contractmodel/blob/main/README.md).

## New users

1. **[Getting started](tutorials/getting-started.md)** — load ODCS, validate data, diff contracts
2. **[CLI walkthrough](tutorials/cli-walkthrough.md)** — `contract validate`, `diff`, `export`
3. **[Examples](https://github.com/eddiethedean/contractmodel/blob/main/examples/README.md)** — bundled contracts and sample data (`pip install` and git clone)

## Reference

| Topic | Document |
|-------|----------|
| **Public API** | [API reference](reference/api.md) |
| **Validation errors** | [CM_* error codes](reference/error-codes.md) |
| **CLI ↔ library** | [Command mapping](reference/cli-library-map.md) |
| **Stability policy** | [STABILITY.md](https://github.com/eddiethedean/contractmodel/blob/main/STABILITY.md) |
| **Security** | [SECURITY.md](https://github.com/eddiethedean/contractmodel/blob/main/SECURITY.md) |

## Tutorials

| Tutorial | Description |
|----------|-------------|
| [Getting started](tutorials/getting-started.md) | ODCS import, CSV validation, breaking changes |
| [CLI walkthrough](tutorials/cli-walkthrough.md) | End-to-end CLI workflows |
| [Pydantic round-trip](tutorials/pydantic-roundtrip.md) | Model → contract → model |
| [Diff workflow](tutorials/diff-workflow.md) | Version comparison in CI |
| [CI with SARIF](tutorials/ci-sarif.md) | GitHub Actions and SARIF output |

## Architecture and specifications

- [System overview](architecture/01-system-overview.md)
- [Canonical Contract Model](architecture/02-canonical-contract-model.md)
- [Roadmap (0.2 → 1.0)](ROADMAP.md)
- [Upgrade plan](CONTRACTMODEL_UPGRADE_PLAN.md)
- [Historical bootstrap phases](roadmap/01-implementation-roadmap.md)
- [Data contract formats](roadmap/03-data-contract-formats.md)

Contributor specifications live in the repository under `docs/specifications/` (not published to this site).

## Contributing

See [CONTRIBUTING.md](https://github.com/eddiethedean/contractmodel/blob/main/CONTRIBUTING.md) and [CODE_OF_CONDUCT.md](https://github.com/eddiethedean/contractmodel/blob/main/CODE_OF_CONDUCT.md).
