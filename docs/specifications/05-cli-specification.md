# ContractCLI Specification

## Command Name

`contract`

## Commands

### init

```bash
contract init
contract init --template odcs
contract init --template fastapi
```

### validate

```bash
contract validate contract.yaml data.csv
contract validate contract.yaml data.parquet
contract validate contract.yaml data.json
```

Options:
- --format csv|json|parquet
- --mode strict|permissive|schema-only|quality-only
- --output text|json|sarif
- --fail-on-warning

### diff

```bash
contract diff old.yaml new.yaml
```

Options:
- --mode backward|forward|full
- --output text|json|markdown

### export

```bash
contract export contract.yaml --to json-schema
contract export contract.yaml --to markdown
contract export contract.yaml --to odcs
contract export contract.yaml --to shacl
```

### generate

```bash
contract generate pydantic contract.yaml --output models.py
```

### publish

```bash
contract publish contract.yaml --registry https://contracthub.example.com
```

### doctor

```bash
contract doctor
```

Checks:
- Python version
- Optional dependencies
- Plugin discovery
- Registry configuration

## Exit Codes

- 0 success
- 1 validation/diff failure
- 2 invalid contract
- 3 IO error
- 4 plugin error
- 5 registry error
