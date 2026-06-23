# ODCS, CCM, and Pydantic Mapping Specification

## Principle

ODCS is an external contract format. Pydantic is an execution engine. The CCM is the internal truth.

```text
ODCS -> CCM -> Pydantic
Pydantic -> CCM -> ODCS
```

## Logical Type Mapping

| CCM Logical Type | Python Type | Pydantic Type |
|---|---|---|
| string | str | str |
| integer | int | int |
| number | float | float |
| decimal | Decimal | Decimal |
| boolean | bool | bool |
| date | datetime.date | date |
| time | datetime.time | time |
| datetime | datetime.datetime | datetime |
| duration | datetime.timedelta | timedelta |
| array | list[T] | list[T] |
| object | dict / nested model | nested BaseModel |
| map | dict[str, T] | dict[str, T] |
| binary | bytes | bytes |
| uuid | uuid.UUID | UUID |
| uri | pydantic.AnyUrl | AnyUrl |
| email | pydantic.EmailStr | EmailStr |
| enum | Enum | Enum |
| any | Any | Any |

## Required and Nullable Rules

| CCM Required | CCM Nullable | Pydantic Annotation |
|---|---|---|
| true | false | field: T |
| true | true | field: T \| None |
| false | false | field: T = default |
| false | true | field: T \| None = None |

## Constraints

| CCM Constraint | Pydantic Mapping |
|---|---|
| min_value | Field(ge=value) |
| max_value | Field(le=value) |
| min_length | Field(min_length=value) |
| max_length | Field(max_length=value) |
| pattern | Field(pattern=value) |
| enum_values | Enum class |
| unique | dataset-level validation |
| immutable | diff/evolution validation |
| allowed_values | custom validator or Enum |
| disallowed_values | custom validator |

## Metadata Preservation

Every adapter must preserve unknown fields under `extensions`.

## Round-Trip Rules

A contract loaded from ODCS and exported back to ODCS must preserve:
- Contract identity
- Version
- Field names
- Types
- Nullability
- Requiredness
- Descriptions
- Ownership
- Quality rules where representable
- Extensions

Lossy transformations must be explicitly reported.
