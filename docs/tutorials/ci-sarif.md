# CI with SARIF

Emit SARIF from `contract validate` for GitHub Code Scanning or other SARIF consumers.

## Local SARIF

```bash
contract validate examples/customer_events.odcs.yaml bad_data.json --output sarif > results.sarif
```

Rule IDs match `CM_*` validation codes — see [error code catalog](../reference/error-codes.md).

## GitHub Actions example

```yaml
name: Validate data contract

on: [pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install ContractModel
        run: pip install "contractmodel[pandas]"

      - name: Validate sample data
        run: |
          contract validate \
            examples/customer_events.odcs.yaml \
            examples/data/customer_event.json \
            --output sarif > sarif-results.sarif

      - name: Upload SARIF
        uses: github/codeql-action/upload-sarif@v3
        if: always()
        with:
          sarif_file: sarif-results.sarif
```

## Programmatic validation

```python
from contractmodel import DataContract, ValidationMode
from contractmodel.examples import load_example
from contractmodel.validation.sarif import validation_result_to_sarif

contract = load_example("customer_events.odcs.yaml")
result = contract.validate_record({"customer_id": "only"}, mode=ValidationMode.STRICT)
sarif = validation_result_to_sarif(result)
```
