# Canonical Contract Model

The Canonical Contract Model, or CCM, is the center of ContractModel.

## Design Goals

- Stable internal representation.
- Independent of ODCS, Pydantic, JSON Schema, Avro, SQL, or vendor-specific tools.
- Easy to serialize to JSON and YAML.
- Easy to validate with Pydantic V2.
- Extensible through metadata and extensions.
- Strong enough to represent schemas, quality rules, SLAs, lineage, governance, and semantic mappings.

## Top-Level Model

```python
class CanonicalContract(BaseModel):
    contract_id: str
    name: str
    version: str
    kind: ContractKind = ContractKind.DATASET
    description: str | None = None
    status: ContractStatus = ContractStatus.DRAFT

    ownership: Ownership | None = None
    schema: ContractSchema
    quality: QualitySpec | None = None
    service_level: ServiceLevelSpec | None = None
    lineage: LineageSpec | None = None
    semantics: SemanticSpec | None = None
    governance: GovernanceSpec | None = None

    metadata: dict[str, Any] = Field(default_factory=dict)
    extensions: dict[str, Any] = Field(default_factory=dict)
```

## Contract Kinds

```python
class ContractKind(str, Enum):
    DATASET = "dataset"
    TABLE = "table"
    FILE = "file"
    STREAM = "stream"
    EVENT = "event"
    API_PAYLOAD = "api_payload"
    SEMANTIC_ENTITY = "semantic_entity"
```

## Contract Status

```python
class ContractStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    RETIRED = "retired"
```

## Schema

```python
class ContractSchema(BaseModel):
    fields: list[ContractField]
    primary_key: list[str] = Field(default_factory=list)
    indexes: list[IndexSpec] = Field(default_factory=list)
    constraints: list[SchemaConstraint] = Field(default_factory=list)
```

## Field

```python
class ContractField(BaseModel):
    name: str
    logical_type: LogicalType
    required: bool = True
    nullable: bool = False

    description: str | None = None
    aliases: list[str] = Field(default_factory=list)

    default: Any | None = None
    examples: list[Any] = Field(default_factory=list)

    constraints: FieldConstraints = Field(default_factory=FieldConstraints)
    children: list["ContractField"] = Field(default_factory=list)

    semantic: SemanticMapping | None = None

    metadata: dict[str, Any] = Field(default_factory=dict)
    extensions: dict[str, Any] = Field(default_factory=dict)
```

## Logical Types

```python
class LogicalType(str, Enum):
    STRING = "string"
    INTEGER = "integer"
    NUMBER = "number"
    DECIMAL = "decimal"
    BOOLEAN = "boolean"
    DATE = "date"
    TIME = "time"
    DATETIME = "datetime"
    DURATION = "duration"
    ARRAY = "array"
    OBJECT = "object"
    MAP = "map"
    BINARY = "binary"
    UUID = "uuid"
    URI = "uri"
    EMAIL = "email"
    ENUM = "enum"
    ANY = "any"
```

## Constraint Model

```python
class FieldConstraints(BaseModel):
    min_value: int | float | Decimal | None = None
    max_value: int | float | Decimal | None = None
    min_length: int | None = None
    max_length: int | None = None
    pattern: str | None = None
    enum_values: list[Any] | None = None
    unique: bool = False
    immutable: bool = False
    allowed_values: list[Any] | None = None
    disallowed_values: list[Any] | None = None
    custom: list[CustomConstraint] = Field(default_factory=list)
```

## Key Rule

All adapters must convert into the CCM first. No validation engine, exporter, or plugin should depend directly on ODCS structures.

## Wire identity (`contractmodel.ccm/1`)

0.2 publishes a versioned wire schema (`CCM_WIRE_VERSION`) and packaged JSON
Schema via `export_ccm_json_schema()`. Integrators should prefer immutable
`describe_contract` descriptors and `fingerprint_contract` over mutating live
`CanonicalContract` instances or walking Pydantic `model_fields`. New format
adapters wait for the **0.4** fidelity protocol.

