# CLI walkthrough

The `contract` command ships with `pip install contractmodel`. This tutorial uses bundled examples.

## Validate JSON

```bash
# Resolve paths from Python (works after pip install)
CONTRACT=$(python -c "from contractmodel.examples import example_path; print(example_path('customer_events.odcs.yaml'))")
DATA=$(python -c "from contractmodel.examples import example_path; print(example_path('data/customer_event.json'))")

contract validate "$CONTRACT" "$DATA"
```

From a git clone:

```bash
contract validate examples/customer_events.odcs.yaml examples/data/customer_event.json
```

## Validate CSV

Requires `contractmodel[pandas]`:

```bash
contract validate examples/customer_events.odcs.yaml examples/data/events.csv --format csv
```

## SARIF output for CI

```bash
contract validate examples/customer_events.odcs.yaml examples/data/bad.json --output sarif
```

See [CI with SARIF](ci-sarif.md) for a GitHub Actions example.

## Diff two contract versions

```bash
contract diff examples/customer_events.ccm.yaml examples/nested_schema.ccm.yaml
```

## Generate Pydantic models

```bash
contract generate pydantic examples/customer_events.odcs.yaml --output models.py
```

## Export formats

```bash
contract export examples/customer_events.odcs.yaml --to json-schema
contract export examples/customer_events.odcs.yaml --to markdown
contract export examples/customer_events.odcs.yaml --to shacl  # requires [semantic]
```

## Doctor

List installed plugins without loading plugin code:

```bash
contract doctor
```
