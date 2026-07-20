# Repository layout

Current layout for ContractModel 0.2.x. Active release plan:
[ROADMAP.md](../../ROADMAP.md).

```text
contractmodel/
  pyproject.toml
  README.md
  ROADMAP.md              # 0.2 → 1.0 release plan
  CONTRIBUTING.md
  CODE_OF_CONDUCT.md
  STABILITY.md
  SECURITY.md
  CHANGELOG.md
  mkdocs.yml
  LICENSE
  src/
    contractmodel/
      __init__.py
      contract.py          # DataContract facade
      examples.py          # Bundled example helpers
      model.py             # ContractModel base for generated Pydantic
      canonical.py         # Canonical JSON / CCM dict helpers
      fingerprint.py
      recognition.py
      policy.py            # LoadingPolicy
      wire.py              # contractmodel.ccm/1 helpers
      versions.py          # ODCS / package version constants
      extensions.py
      errors.py
      descriptor/          # Immutable ContractDescriptor stack
      schemas/ccm/v1/      # Packaged CCM JSON Schema
      core/
        ccm.py
        types.py
        constraints.py
        result.py
      adapters/
        odcs.py
        odcs_conformance.py  # pyodcs validate / parse / diff_odcs
        pydantic.py
      validation/
        engine.py
        dataframe.py
        quality.py
        sarif.py
      diff/
        engine.py
        rules.py
      export/
        markdown.py
        json_schema.py
        openapi.py
        odcs.py
        registry.py        # export_stability
      cli/
        app.py
      plugins/
        manager.py
        protocols.py
        runtime.py
      registry/
        client.py
      semantic/
        rdf.py
        shacl.py
        owl.py
      examples_data/       # Mirror of repository examples/ (shipped in wheel)
      py.typed
  tests/
  examples/
    README.md
    data/
  docs/
    README.md
    ROADMAP.md            # Symlink to ../ROADMAP.md (MkDocs)
    CONTRACTMODEL_UPGRADE_PLAN.md
    tutorials/
    reference/
    architecture/
    specifications/
    roadmap/
    internal/
  .github/
    workflows/
    ISSUE_TEMPLATE/
```

## Optional dependencies

CLI dependencies (`typer`, `rich`) are included in the base install. Optional validation and export extras:

```toml
[project.optional-dependencies]
pandas = ["pandas>=2.0"]
polars = ["polars>=0.20"]
parquet = ["pyarrow>=15.0"]
semantic = ["rdflib>=7.0"]
all = ["pandas>=2.0", "polars>=0.20", "pyarrow>=15.0", "rdflib>=7.0"]
```

Dev tools are in `[dependency-groups] dev` (pytest, ruff, mypy, pre-commit, mkdocs).

## Examples packaging

Repository `examples/` must be kept in sync with `src/contractmodel/examples_data/` manually (see `tests/test_examples.py::test_examples_dirs_stay_in_sync`). Use `contractmodel.examples.load_example()` after `pip install`.
