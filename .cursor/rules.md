# ContractModel Rules

## Architecture

- All external formats (ODCS, Pydantic, JSON Schema, etc.) must convert through the Canonical Contract Model (CCM).
- No validation engine, exporter, or plugin may depend directly on ODCS structures.

## Dependencies

- Core package: only `pydantic` and `pyyaml`.
- Heavy integrations (pandas, polars, pyarrow, typer, rdflib) live behind optional extras.

## Code Style

- Pydantic V2 models with full type hints.
- Follow specs in `docs/specifications/` and architecture in `docs/architecture/`.
- Match existing naming and module layout in `docs/specifications/10-repository-layout.md`.

## Testing

- Every bug fix includes a regression test.
- Use fixtures in `examples/` where applicable.
