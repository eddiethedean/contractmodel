# Repository layout

Current layout for ContractModel 0.1.x.

```text
contractmodel/
  pyproject.toml
  README.md
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
      model.py
      errors.py
      core/
        ccm.py
        types.py
        constraints.py
        result.py
      adapters/
        odcs.py
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
  tests/
  examples/
    README.md
    data/
  docs/
    README.md
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
