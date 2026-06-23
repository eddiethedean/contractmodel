# ContractHub Architecture and API

## Purpose

ContractHub is the optional registry/catalog layer.

## Core Entities

- Contract
- ContractVersion
- CompatibilityReport
- Producer
- Consumer
- Dependency
- ValidationRun

## REST API

### List Contracts

```http
GET /contracts
```

### Get Contract

```http
GET /contracts/{contract_id}
```

### Publish Version

```http
POST /contracts/{contract_id}/versions
```

### Diff Versions

```http
POST /contracts/{contract_id}/diff
```

### Compatibility Check

```http
POST /contracts/{contract_id}/compatibility
```

## Storage Model

Recommended tables:
- contracts
- contract_versions
- contract_dependencies
- validation_runs
- compatibility_reports

## Auth

v1:
- Token-based auth.

Future:
- OIDC
- SSO
- Fine-grained RBAC
