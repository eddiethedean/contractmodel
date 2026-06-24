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
from contractmodel.core.result import ValidationResult, ValidationWarningDetail
from contractmodel.core.types import CompatibilityMode, ValidationMode
from contractmodel.diff.engine import ContractDiff, diff_contracts
from contractmodel.export.json_schema import export_json_schema
from contractmodel.export.markdown import export_markdown
from contractmodel.export.openapi import export_openapi
from contractmodel.plugins.runtime import run_validator_plugins
from contractmodel.semantic.owl import export_owl
from contractmodel.semantic.rdf import export_rdf
from contractmodel.semantic.shacl import export_shacl
from contractmodel.validation import dataframe as dataframe_validation
from contractmodel.validation import engine as validation_engine


class DataContract:
    """User-facing wrapper around the Canonical Contract Model."""

    def __init__(
        self,
        ccm: CanonicalContract,
        *,
        import_warnings: list[ValidationWarningDetail] | None = None,
    ) -> None:
        self._ccm = ccm
        self._import_warnings = import_warnings or []
        self._pydantic_models: dict[str | None, type[BaseModel]] = {}

    @classmethod
    def from_yaml(cls, path: str | Path) -> DataContract:
        with Path(path).open() as f:
            data = yaml.safe_load(f)
        if not isinstance(data, dict):
            msg = "Contract YAML must contain a mapping"
            raise ValueError(msg)
        if is_odcs_document(data):
            return cls.from_odcs_dict(data)
        return cls(CanonicalContract.model_validate(data))

    @classmethod
    def from_json(cls, path: str | Path) -> DataContract:
        with Path(path).open() as f:
            data = json.load(f)
        if not isinstance(data, dict):
            msg = "Contract JSON must contain an object"
            raise ValueError(msg)
        if is_odcs_document(data):
            return cls.from_odcs_dict(data)
        return cls(CanonicalContract.model_validate(data))

    @classmethod
    def from_odcs(cls, path: str | Path) -> DataContract:
        with Path(path).open() as f:
            data = yaml.safe_load(f)
        if not isinstance(data, dict):
            msg = "ODCS document must be a mapping"
            raise ValueError(msg)
        return cls.from_odcs_dict(data)

    @classmethod
    def from_odcs_dict(cls, data: dict[str, Any]) -> DataContract:
        warnings: list[ValidationWarningDetail] = []
        owner = data.get("owner")
        if isinstance(owner, dict) and owner.get("contact"):
            warnings.append(
                ValidationWarningDetail(
                    code="ODCS_LOSSY_IMPORT",
                    message=(
                        "ODCS contact imported as ownership contact list; "
                        "export uses first contact only"
                    ),
                )
            )
        return cls(import_odcs(data), import_warnings=warnings)

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
    def import_warnings(self) -> list[ValidationWarningDetail]:
        return self._import_warnings

    @property
    def name(self) -> str:
        return self._ccm.name

    @property
    def version(self) -> str:
        return self._ccm.version

    @property
    def fields(self) -> list[ContractField]:
        return self._ccm.contract_schema.fields

    def to_pydantic(self, *, class_name: str | None = None) -> type[BaseModel]:
        if class_name not in self._pydantic_models:
            self._pydantic_models[class_name] = generate_pydantic_model(
                self._ccm,
                class_name=class_name,
            )
        return self._pydantic_models[class_name]

    def validate_record(
        self,
        record: Mapping[str, Any],
        *,
        mode: ValidationMode = ValidationMode.STRICT,
    ) -> ValidationResult:
        result = validation_engine.validate_record(self._ccm, record, mode=mode)
        return run_validator_plugins(self._ccm, dict(record), result)

    def validate_records(
        self,
        records: Iterable[Mapping[str, Any]],
        *,
        mode: ValidationMode = ValidationMode.STRICT,
    ) -> ValidationResult:
        record_list = list(records)
        result = validation_engine.validate_records(self._ccm, record_list, mode=mode)
        return run_validator_plugins(self._ccm, record_list, result)

    def validate_json(
        self,
        data: str | bytes | Mapping[str, Any] | list[Mapping[str, Any]],
        *,
        mode: ValidationMode = ValidationMode.STRICT,
    ) -> ValidationResult:
        result = validation_engine.validate_json(self._ccm, data, mode=mode)
        plugin_data: Any = data
        if isinstance(data, (str, bytes)):
            try:
                plugin_data = json.loads(data)
            except json.JSONDecodeError:
                plugin_data = data
        return run_validator_plugins(self._ccm, plugin_data, result)

    def validate_csv(
        self,
        path: str | Path,
        *,
        mode: ValidationMode = ValidationMode.STRICT,
        **kwargs: Any,
    ) -> ValidationResult:
        result = dataframe_validation.validate_csv(self._ccm, path, mode=mode, **kwargs)
        return run_validator_plugins(self._ccm, str(path), result)

    def validate_parquet(
        self,
        path: str | Path,
        *,
        mode: ValidationMode = ValidationMode.STRICT,
        **kwargs: Any,
    ) -> ValidationResult:
        result = dataframe_validation.validate_parquet(self._ccm, path, mode=mode, **kwargs)
        return run_validator_plugins(self._ccm, str(path), result)

    def validate_pandas(
        self,
        df: Any,
        *,
        mode: ValidationMode = ValidationMode.STRICT,
    ) -> ValidationResult:
        result = dataframe_validation.validate_pandas(self._ccm, df, mode=mode)
        return run_validator_plugins(self._ccm, df, result)

    def validate_polars(
        self,
        df: Any,
        *,
        mode: ValidationMode = ValidationMode.STRICT,
    ) -> ValidationResult:
        result = dataframe_validation.validate_polars(self._ccm, df, mode=mode)
        return run_validator_plugins(self._ccm, df, result)

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

    def to_openapi(self) -> dict[str, Any]:
        return export_openapi(self._ccm)

    def to_markdown(self) -> str:
        return export_markdown(self._ccm)

    def to_rdf(self) -> str:
        return export_rdf(self._ccm)

    def to_shacl(self) -> str:
        return export_shacl(self._ccm)

    def to_owl(self) -> str:
        return export_owl(self._ccm)
