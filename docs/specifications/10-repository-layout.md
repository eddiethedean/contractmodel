# Repository Layout

```text
contractmodel/
  pyproject.toml
  README.md
  LICENSE
  src/
    contractmodel/
      __init__.py
      core/
        ccm.py
        types.py
        constraints.py
        result.py
      adapters/
        odcs.py
        pydantic.py
        json_schema.py
      validation/
        engine.py
        dataframe.py
        quality.py
      diff/
        engine.py
        rules.py
      export/
        markdown.py
        json_schema.py
        openapi.py
        semantic.py
      cli/
        app.py
      plugins/
        manager.py
        protocols.py
      registry/
        client.py
      semantic/
        rdf.py
        shacl.py
        owl.py
  tests/
  examples/
  docs/
```

## Optional Dependencies

```toml
[project.optional-dependencies]
pandas = ["pandas"]
polars = ["polars"]
parquet = ["pyarrow"]
cli = ["typer", "rich"]
semantic = ["rdflib"]
all = ["pandas", "polars", "pyarrow", "typer", "rich", "rdflib"]
```
