# Security Policy

## Reporting vulnerabilities

Report security issues privately to the repository maintainers via GitHub Security Advisories or direct contact listed on the project page. Do not open public issues for undisclosed vulnerabilities.

## Dependency and install trust

- Install only from [PyPI](https://pypi.org/project/contractmodel/) or trusted source builds.
- Optional extras (`pandas`, `polars`, `parquet`, `semantic`) pull additional third-party packages; review their security posture for your environment.
- The `contract` CLI is installed with the base package and depends on Typer and Rich.

## Contract and data files

- Contract YAML is loaded with `yaml.safe_load` (no arbitrary object deserialization).
- Validation reads entire data files (JSON, CSV, Parquet) into memory. For untrusted uploads, enforce size limits in your application layer. Recommended starting point: **≤ 100 MB per file** and **≤ 1 million rows** per validation run on 0.1.x.

## Registry publish

- `contract publish` and `publish_contract()` send the full contract JSON to the URL you configure.
- Use HTTPS endpoints you trust.
- Set `CONTRACT_REGISTRY_TOKEN` to send `Authorization: Bearer <token>` when your registry requires authentication.
- The client does not verify registry identity beyond TLS. Treat the registry URL like a webhook secret endpoint.

## Plugins

- Plugins are loaded from Python entry points in installed packages. Only install plugins from trusted sources.
- `contract doctor` lists plugin names without loading plugin code. Plugins are loaded when validation, export, or publish runs.

## Generated scaffolds

- `contract init --template fastapi` creates a minimal API without authentication or CORS hardening. Do not expose generated apps to the public internet without adding appropriate controls.

## Supported versions

Security fixes are applied to the latest **0.1.x** release. Upgrade to the newest patch when available.
