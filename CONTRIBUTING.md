# Contributing to ContractModel

Thank you for your interest in contributing. This guide covers local setup, quality checks, and pull request expectations.

## Prerequisites

- Python 3.10, 3.11, or 3.12
- Git

## Development setup

```bash
git clone https://github.com/eddiethedean/contractmodel.git
cd contractmodel
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[all]" --group dev
pre-commit install
```

With [uv](https://docs.astral.sh/uv/):

```bash
uv sync --group dev --extra all
```

Dev tools (`pytest`, `ruff`, `mypy`, `pre-commit`, `mkdocs`) live in the `[dependency-groups] dev` section of `pyproject.toml`. Do not install them separately unless debugging.

## Quality checks

Run the same checks as CI before opening a PR:

```bash
ruff check src tests
mypy src
pytest
```

Optional: build docs locally:

```bash
mkdocs serve
```

## Project layout

- `src/contractmodel/` — library source
- `tests/` — pytest suite (mirrors package structure)
- `examples/` — sample contracts and data (bundled into the wheel)
- `docs/` — user docs, tutorials, and contributor specifications
- `ROADMAP.md` — active 0.2 → 1.0 release plan

See [docs/specifications/10-repository-layout.md](docs/specifications/10-repository-layout.md) for the full tree.

## Priorities

Follow **[ROADMAP.md](ROADMAP.md)** when choosing what to build next:

1. **0.2** — shipped (semantic kernel, descriptors, fingerprints, loading policy, pyodcs)
2. **0.3** — bounded validation protocol
3. **0.4** — adapter/fidelity framework, then new formats
4. Compatibility (**0.5**), trust (**0.6**), CLI/DX (**0.7**), conformance (**0.8**)

Prefer semantic depth over new format adapters. Design detail:
[`docs/CONTRACTMODEL_UPGRADE_PLAN.md`](docs/CONTRACTMODEL_UPGRADE_PLAN.md).

## Releasing

1. Confirm `pyproject.toml` and `contractmodel.__version__` match (e.g. `0.2.0`).
2. Ensure `CHANGELOG.md` has a dated section for that version; keep forward-looking limits under **Unreleased**.
3. Run `ruff check src tests`, `mypy src`, and `pytest`.
4. Optionally `python -m build && twine check dist/*`.
5. Tag `vX.Y.Z` on `main` and push the tag. The [release workflow](.github/workflows/release.yml) runs CI on 3.10–3.12, verifies the tag matches `pyproject.toml`, then publishes to PyPI (`PYPI_API_TOKEN`).

## Pull requests

1. Fork and create a feature branch from `main`
2. Add or update tests for behavior changes
3. Update `CHANGELOG.md` under **Unreleased** for user-visible changes
4. Ensure CI passes (ruff, mypy, pytest on 3.10–3.12)
5. Fill out the PR template

Keep changes focused. Prefer extending existing modules over new abstractions.

## Cursor / AI-assisted development

Internal prompts and rules live under `.cursor/` and `docs/internal/`. They are contributor aids, not end-user documentation.

## Code of conduct

This project follows the [Contributor Covenant](CODE_OF_CONDUCT.md). Please read it before participating.

## Questions

Open a [GitHub issue](https://github.com/eddiethedean/contractmodel/issues) for bugs, feature requests, or design discussion.
