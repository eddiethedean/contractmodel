# Cursor Implementation Prompt

You are building ContractModel, a Python-native data contract framework.

Read these documents first:

1. docs/architecture/01-system-overview.md
2. docs/architecture/02-canonical-contract-model.md
3. docs/specifications/01-public-api.md
4. docs/specifications/02-odcs-pydantic-mapping.md
5. docs/roadmap/01-implementation-roadmap.md
6. .cursor/rules.md

## Task

Implement the project in phases. Do not skip phases.

## Phase 1

Create the repository skeleton and implement the Canonical Contract Model.

Requirements:
- Pydantic V2 models.
- Full type hints.
- Unit tests.
- No optional heavy dependencies in core.

## Phase 2

Implement ODCS YAML import and export.

## Phase 3

Implement Pydantic model generation.

## Phase 4

Implement validation.

## Phase 5

Implement DataFrame support behind optional extras.

## Phase 6

Implement diff engine and CLI.

## Constraints

All external representations must map through the CCM.

Do not invent incompatible APIs. Follow the specs.
