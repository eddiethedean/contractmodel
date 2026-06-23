"""Core type enumerations for ContractModel."""

from enum import Enum


class ContractKind(str, Enum):
    DATASET = "dataset"
    TABLE = "table"
    FILE = "file"
    STREAM = "stream"
    EVENT = "event"
    API_PAYLOAD = "api_payload"
    SEMANTIC_ENTITY = "semantic_entity"


class ContractStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    RETIRED = "retired"


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


class ValidationMode(str, Enum):
    STRICT = "strict"
    PERMISSIVE = "permissive"
    SCHEMA_ONLY = "schema_only"
    QUALITY_ONLY = "quality_only"


class CompatibilityMode(str, Enum):
    BACKWARD = "backward"
    FORWARD = "forward"
    FULL = "full"
    NONE = "none"
