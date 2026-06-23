"""DataContract user-facing facade."""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel

from contractmodel.adapters.odcs import export_odcs, import_odcs, is_odcs_document
from contractmodel.adapters.pydantic import contract_from_pydantic, generate_pydantic_model
from contractmodel.core.ccm import CanonicalContract, ContractField
from contractmodel.core.result import ValidationResult
from contractmodel.core.types import CompatibilityMode, ValidationMode
from contractmodel.diff.engine import ContractDiff, diff_contracts
from contractmodel.export.markdown import export_json_schema, export_markdown
from contractmodel.validation import dataframe as dataframe_validation
from contractmodel.validation import engine as validation_engine


class DataContract:
    """User-facing wrapper around the Canonical Contract Model."""

    def __init__(self, ccm: CanonicalContract) -> None:
        self._ccm = ccm

    @classmethod
    def from_yaml(cls, path: str | Path) -> DataContract:
        with Path(path).open() as f:
            data = yaml.safe_load(f)
        if not isinstance(data, dict):
            msg = "Contract YAML must contain a mapping"
            raise ValueError(msg)
        if is_odcs_document(data):
            return cls(import_odcs(data))
        return cls(CanonicalContract.model_validate(data))

    @classmethod
    def from_json(cls, path: str | Path) -> DataContract:
        with Path(path).open() as f:
            data = json.load(f)
        if not isinstance(data, dict):
            msg = "Contract JSON must contain an object"
            raise ValueError(msg)
        if is_odcs_document(data):
            return cls(import_odcs(data))
        return cls(CanonicalContract.model_validate(data))

    @classmethod
    def from_odcs(cls, path: str | Path) -> DataContract:
        with Path(path).open() as f:
            data = yaml.safe_load(f)
        if not isinstance(data, dict):
            msg = "ODCS document must be a mapping"
            raise ValueError(msg)
        return cls(import_odcs(data))

    @classmethod
    def from_pydantic(cls, model: type[BaseModel], *, name: str | None = None) -> DataContract:
        return cls(contract_from_pydantic(model, name=name))

    @classmethod
    def from_ccm(cls, ccm: CanonicalContract) -> DataContract:
        return cls(ccm)

    @property
    def ccm(self) -> CanonicalContract:
        return self._ccm

    @property
    def name(self) -> str:
        return self._ccm.name

    @property
    def version(self) -> str:
        return self._ccm.version

    @property
    def fields(self) -> list[ContractField]:
        return self._ccm.schema.fields

    def to_pydantic(self, *, class_name: str | None = None) -> type[BaseModel]:
        return generate_pydantic_model(self._ccm, class_name=class_name)

    def validate_record(
        self,
        record: Mapping[str, Any],
        *,
        mode: ValidationMode = ValidationMode.STRICT,
    ) -> ValidationResult:
        return validation_engine.validate_record(self._ccm, record, mode=mode)

    def validate_records(
        self,
        records: Iterable[Mapping[str, Any]],
        *,
        mode: ValidationMode = ValidationMode.STRICT,
    ) -> ValidationResult:
        return validation_engine.validate_records(self._ccm, records, mode=mode)

    def validate_json(
        self,
        data: str | bytes | Mapping[str, Any] | list[Mapping[str, Any]],
        *,
        mode: ValidationMode = ValidationMode.STRICT,
    ) -> ValidationResult:
        return validation_engine.validate_json(self._ccm, data, mode=mode)

    def validate_csv(
        self,
        path: str | Path,
        *,
        mode: ValidationMode = ValidationMode.STRICT,
        **kwargs: Any,
    ) -> ValidationResult:
        return dataframe_validation.validate_csv(self._ccm, path, mode=mode, **kwargs)

    def validate_parquet(
        self,
        path: str | Path,
        *,
        mode: ValidationMode = ValidationMode.STRICT,
        **kwargs: Any,
    ) -> ValidationResult:
        return dataframe_validation.validate_parquet(self._ccm, path, mode=mode, **kwargs)

    def validate_pandas(
        self,
        df: Any,
        *,
        mode: ValidationMode = ValidationMode.STRICT,
    ) -> ValidationResult:
        return dataframe_validation.validate_pandas(self._ccm, df, mode=mode)

    def validate_polars(
        self,
        df: Any,
        *,
        mode: ValidationMode = ValidationMode.STRICT,
    ) -> ValidationResult:
        return dataframe_validation.validate_polars(self._ccm, df, mode=mode)

    def diff(
        self,
        other: DataContract,
        *,
        mode: CompatibilityMode = CompatibilityMode.BACKWARD,
    ) -> ContractDiff:
        return diff_contracts(self._ccm, other._ccm, mode=mode)

    def is_breaking_change(
        self,
        other: DataContract,
        *,
        mode: CompatibilityMode = CompatibilityMode.BACKWARD,
    ) -> bool:
        return self.diff(other, mode=mode).is_breaking

    def to_odcs(self) -> dict[str, Any]:
        return export_odcs(self._ccm)

    def to_json_schema(self) -> dict[str, Any]:
        return export_json_schema(self._ccm)

    def to_markdown(self) -> str:
        return export_markdown(self._ccm)

    def to_rdf(self) -> str:
        return f"# RDF export stub for {self._ccm.contract_id}\n"

    def to_shacl(self) -> str:
        return f"# SHACL export stub for {self._ccm.contract_id}\n"

    def to_owl(self) -> str:
        return f"# OWL export stub for {self._ccm.contract_id}\n"
