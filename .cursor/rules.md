# ContractModel Rules

## Architecture

- All external formats (ODCS, Pydantic, JSON Schema, etc.) must convert through the Canonical Contract Model (CCM).
- No validation engine, exporter, or plugin may depend directly on ODCS structures.
- ContractModel never imports ETLantic, pipeline plans, or execution plugins.

## Priorities

Follow root **ROADMAP.md** (detail in `docs/CONTRACTMODEL_UPGRADE_PLAN.md`):

1. Prefer semantic kernel / integration API work (**0.2**) over new format adapters.
2. Bounded validation and evidence (**0.3**) before expanding engines.
3. Adapter/fidelity framework (**0.4**) before Avro, Protobuf, dbt, lakehouse, etc.
4. Prefer semantic depth over integration count.

## Dependencies

- Core package: only `pydantic` and `pyyaml`.
- Heavy integrations (pandas, polars, pyarrow, typer, rdflib) live behind optional extras.
- Do not add optional engines or registry code to the core import path.

## Integration surface

- Public top-level APIs only for downstream integrators.
- Do not treat `contractmodel.validation.limits` or generated `model_fields` as the supported consumer contract; those are replaced by the 0.2 descriptor and loading-policy APIs.

## Code Style

- Pydantic V2 models with full type hints.
- Follow specs in `docs/specifications/` and architecture in `docs/architecture/`.
- Match existing naming and module layout in `docs/specifications/10-repository-layout.md`.

## Testing

- Every bug fix includes a regression test.
- Use fixtures in `examples/` where applicable.
