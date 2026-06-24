# CLI ↔ library mapping

| CLI command | Library equivalent |
|-------------|-------------------|
| `contract validate CONTRACT DATA` | `DataContract.from_yaml(CONTRACT).validate_json(...)` or `validate_csv` / `validate_parquet` by `--format` |
| `contract validate ... --output sarif` | `validation_result_to_sarif(result)` from `contractmodel.validation.sarif` |
| `contract diff OLD NEW` | `old.diff(new)` |
| `contract generate pydantic CONTRACT` | `contract.to_pydantic()` |
| `contract export CONTRACT --to json-schema` | `contract.to_json_schema()` |
| `contract export CONTRACT --to openapi` | `contract.to_openapi()` |
| `contract export CONTRACT --to markdown` | `contract.to_markdown()` |
| `contract export CONTRACT --to odcs` | `contract.to_odcs()` |
| `contract export CONTRACT --to shacl` | `contract.to_shacl()` |
| `contract init` | Scaffolds YAML — no direct library call |
| `contract publish` | Registry client (experimental) |
| `contract doctor` | Lists entry-point plugin names |

## Load paths

The CLI accepts any filesystem path. After `pip install`, use bundled examples:

```python
from contractmodel.examples import example_path
path = example_path("customer_events.odcs.yaml")
```

```bash
contract validate "$(python -c 'from contractmodel.examples import example_path; print(example_path(\"customer_events.odcs.yaml\"))')" data.json
```
