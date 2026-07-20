"""DataContract user-facing facade."""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any, Literal, cast

import yaml
from pydantic import BaseModel

from contractmodel.adapters.odcs import (
    collect_odcs_import_warnings,
    export_odcs,
    import_odcs,
    is_odcs_document,
)
from contractmodel.adapters.odcs_conformance import (
    diff_odcs_documents,
    parse_and_validate_odcs_file,
    validate_odcs_document,
)
from contractmodel.adapters.pydantic import (
    contract_from_pydantic,
    get_pydantic_model,
    mode_to_generation_options,
)
from contractmodel.core.ccm import CanonicalContract, ContractField, ContractSchema
from contractmodel.core.result import ValidationResult, ValidationWarningDetail
from contractmodel.core.types import CompatibilityMode, ContractKind, ContractStatus, ValidationMode
from contractmodel.descriptor import describe_contract
from contractmodel.descriptor.models import ContractDescriptor
from contractmodel.diff.engine import ContractDiff, diff_contracts
from contractmodel.errors import OptionalDependencyError
from contractmodel.export.json_schema import export_json_schema
from contractmodel.export.markdown import export_markdown
from contractmodel.export.openapi import export_openapi
from contractmodel.extensions import validate_extensions
from contractmodel.model import ContractModel
from contractmodel.plugins.runtime import run_validator_plugins
from contractmodel.policy import (
    LoadingPolicy,
    enforce_document_bounds,
    resolve_contract_path,
)
from contractmodel.semantic.owl import export_owl
from contractmodel.semantic.rdf import export_rdf
from contractmodel.semantic.shacl import export_shacl
from contractmodel.validation import dataframe as dataframe_validation
from contractmodel.validation import engine as validation_engine
from contractmodel.validation.limits import (
    check_file_byte_limit,
    limit_exceeded_result,
    validate_limit_params,
)
from contractmodel.versions import normalize_odcs_api_version


def _looks_like_odcs_path(path: Path) -> bool:
    """Return True when a path name indicates ODCS YAML (``.odcs``, ``.odcs.yaml``, …)."""
    name = path.name.lower()
    return name.endswith(".odcs") or name.endswith(".odcs.yaml") or name.endswith(".odcs.yml")


def _validate_field_tree_extensions(
    fields: list[ContractField],
    *,
    path_prefix: str = "fields",
) -> None:
    for field in fields:
        validate_extensions(field.extensions, path=f"{path_prefix}.{field.name}.extensions")
        if field.children:
            _validate_field_tree_extensions(
                field.children,
                path_prefix=f"{path_prefix}.{field.name}.children",
            )


class DataContract:
    """User-facing wrapper around the Canonical Contract Model.

    Prefer factory classmethods (``from_yaml``, ``from_dict``, ``from_ccm``) over
    calling ``__init__`` directly so import warnings and format detection run correctly.
    """

    def __init__(
        self,
        ccm: CanonicalContract,
        *,
        import_warnings: list[ValidationWarningDetail] | None = None,
        source_format: str | None = None,
    ) -> None:
        self._ccm = ccm
        self._import_warnings = import_warnings or []
        self._source_format = source_format

    @classmethod
    def load(
        cls,
        path: str | Path,
        *,
        policy: LoadingPolicy | None = None,
    ) -> DataContract:
        """Load a contract from a file (``.yaml``/``.yml`` or ``.json`` by extension)."""
        path = resolve_contract_path(path, policy)
        if path.suffix.lower() == ".json":
            return cls.from_json(path, policy=policy)
        return cls.from_yaml(path, policy=policy)

    @classmethod
    def from_yaml(
        cls,
        path: str | Path,
        *,
        policy: LoadingPolicy | None = None,
    ) -> DataContract:
        """Load CCM or ODCS YAML from a file path (format auto-detected)."""
        path = resolve_contract_path(path, policy)
        with path.open(encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if not isinstance(data, dict):
            msg = "Contract YAML must contain a mapping"
            raise ValueError(msg)
        return cls.from_dict(data, policy=policy)

    @classmethod
    def from_json(
        cls,
        path: str | Path,
        *,
        policy: LoadingPolicy | None = None,
    ) -> DataContract:
        """Load CCM or ODCS JSON from a file path (format auto-detected)."""
        path = resolve_contract_path(path, policy)
        with path.open(encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            msg = "Contract JSON must contain an object"
            raise ValueError(msg)
        return cls.from_dict(data, policy=policy)

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
        *,
        policy: LoadingPolicy | None = None,
    ) -> DataContract:
        """Load a contract from a mapping (CCM or ODCS, auto-detected)."""
        if is_odcs_document(data):
            return cls.from_odcs_dict(data, policy=policy)
        enforce_document_bounds(data, policy, format_name="ccm")
        ccm = CanonicalContract.model_validate(data)
        validate_extensions(ccm.extensions)
        _validate_field_tree_extensions(ccm.contract_schema.fields)
        return cls(ccm, source_format="ccm")

    @classmethod
    def from_odcs(
        cls,
        path: str | Path,
        *,
        policy: LoadingPolicy | None = None,
    ) -> DataContract:
        """Load an ODCS document from a YAML or JSON file path."""
        path = resolve_contract_path(path, policy)
        data = parse_and_validate_odcs_file(path)
        return cls.from_odcs_dict(data, policy=policy, _already_validated=True)

    @classmethod
    def from_odcs_dict(
        cls,
        data: dict[str, Any],
        *,
        policy: LoadingPolicy | None = None,
        _already_validated: bool = False,
    ) -> DataContract:
        """Load an ODCS document from a dict.

        Populates ``import_warnings`` when lossy fields are detected during import.
        Conformance is enforced by pyodcs unless ``_already_validated`` is set.
        """
        api_version = normalize_odcs_api_version(
            data.get("apiVersion") if isinstance(data.get("apiVersion"), str) else None
        )
        enforce_document_bounds(
            data,
            policy,
            format_name="odcs",
            odcs_api_version=api_version,
        )
        if not _already_validated:
            validate_odcs_document(data)
        warnings = [
            ValidationWarningDetail(code="ODCS_LOSSY_IMPORT", message=message)
            for message in collect_odcs_import_warnings(data)
        ]
        return cls(
            import_odcs(data),
            import_warnings=warnings,
            source_format="odcs",
        )

    @classmethod
    def from_pydantic(cls, model: type[BaseModel], *, name: str | None = None) -> DataContract:
        """Build a contract from a Pydantic model class (version defaults to ``1.0.0``)."""
        return cls(contract_from_pydantic(model, name=name), source_format="pydantic")

    @classmethod
    def from_ccm(cls, ccm: CanonicalContract) -> DataContract:
        """Wrap an existing :class:`~contractmodel.core.ccm.CanonicalContract`."""
        return cls(ccm, source_format="ccm")

    @property
    def ccm(self) -> CanonicalContract:
        """Underlying canonical contract model (advanced use)."""
        return self._ccm

    @property
    def import_warnings(self) -> list[ValidationWarningDetail]:
        """Warnings from lossy ODCS import (empty for native CCM loads)."""
        return self._import_warnings

    @property
    def source_format(self) -> str | None:
        """Loader-recorded source format (``ccm``, ``odcs``, ``pydantic``, …)."""
        return self._source_format

    @property
    def contract_id(self) -> str:
        """Stable contract identifier."""
        return self._ccm.contract_id

    @property
    def name(self) -> str:
        """Human-readable contract name."""
        return self._ccm.name

    @property
    def version(self) -> str:
        """Semantic version string."""
        return self._ccm.version

    @property
    def kind(self) -> ContractKind:
        """Contract kind (dataset, table, event, etc.)."""
        return self._ccm.kind

    @property
    def status(self) -> ContractStatus:
        """Lifecycle status (draft, active, deprecated, retired)."""
        return self._ccm.status

    @property
    def schema(self) -> ContractSchema:
        """Full contract schema including indexes and constraints."""
        return self._ccm.contract_schema

    @property
    def fields(self) -> list[ContractField]:
        """Top-level schema fields (shortcut for ``schema.fields``)."""
        return self._ccm.contract_schema.fields

    def describe(self) -> ContractDescriptor:
        """Return an immutable descriptor for integrator introspection."""
        return describe_contract(self)

    def to_pydantic(
        self,
        *,
        class_name: str | None = None,
        mode: ValidationMode = ValidationMode.STRICT,
    ) -> type[ContractModel]:
        """Generate a cached Pydantic model subclassing :class:`~contractmodel.model.ContractModel`.

        Uses the same generation path and cache as ``validate_*`` for the given
        ``mode``. Default ``STRICT`` forbids extra fields and applies constraints.
        """
        schema_only, forbid_extra = mode_to_generation_options(mode)
        return cast(
            type[ContractModel],
            get_pydantic_model(
                self._ccm.model_dump_json(),
                class_name,
                schema_only,
                forbid_extra,
            ),
        )

    def validate(
        self,
        path: str | Path,
        *,
        format: str = "auto",
        mode: ValidationMode = ValidationMode.STRICT,
        max_bytes: int | None = None,
        max_rows: int | None = None,
    ) -> ValidationResult:
        """Validate a data file (format auto-detected from extension when ``format='auto'``).

        Supports ``.csv``, ``.parquet``, and ``.json`` (default for other extensions).
        """
        validate_limit_params(max_bytes=max_bytes, max_rows=max_rows)
        data_path = Path(path)
        try:
            file_limit = check_file_byte_limit(data_path, max_bytes)
            if file_limit is not None:
                return file_limit

            suffix = data_path.suffix.lower()
            resolved_format = format
            if resolved_format == "auto":
                if suffix == ".csv":
                    resolved_format = "csv"
                elif suffix == ".parquet":
                    resolved_format = "parquet"
                else:
                    resolved_format = "json"

            if resolved_format == "csv":
                return self.validate_csv(data_path, mode=mode, max_rows=max_rows)
            if resolved_format == "parquet":
                return self.validate_parquet(data_path, mode=mode, max_rows=max_rows)
            if resolved_format == "json":
                return self.validate_json(
                    data_path.read_text(encoding="utf-8"),
                    mode=mode,
                    max_bytes=max_bytes,
                    max_rows=max_rows,
                )
            msg = f"Unsupported data format: {resolved_format}"
            raise ValueError(msg)
        except ValueError:
            raise
        except OSError as exc:
            return limit_exceeded_result(f"Failed to read data file: {exc}")
        except UnicodeDecodeError as exc:
            return limit_exceeded_result(f"Failed to decode data file: {exc}")

    def validate_record(
        self,
        record: Mapping[str, Any],
        *,
        mode: ValidationMode = ValidationMode.STRICT,
    ) -> ValidationResult:
        """Validate a single record mapping against this contract."""
        result = validation_engine.validate_record(self._ccm, record, mode=mode)
        return run_validator_plugins(self._ccm, dict(record), result)

    def validate_records(
        self,
        records: Iterable[Mapping[str, Any]],
        *,
        mode: ValidationMode = ValidationMode.STRICT,
        max_rows: int | None = None,
    ) -> ValidationResult:
        """Validate an iterable of records (materialized in memory)."""
        validate_limit_params(max_rows=max_rows)
        record_list = list(records)
        result = validation_engine.validate_records(
            self._ccm,
            record_list,
            mode=mode,
            max_rows=max_rows,
        )
        return run_validator_plugins(self._ccm, record_list, result)

    def validate_json(
        self,
        data: str | bytes | Mapping[str, Any] | list[Mapping[str, Any]],
        *,
        mode: ValidationMode = ValidationMode.STRICT,
        max_bytes: int | None = None,
        max_rows: int | None = None,
    ) -> ValidationResult:
        """Validate JSON string/bytes, a dict, or a list of dicts."""
        validate_limit_params(max_bytes=max_bytes, max_rows=max_rows)
        result = validation_engine.validate_json(
            self._ccm,
            data,
            mode=mode,
            max_bytes=max_bytes,
            max_rows=max_rows,
        )
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
        read_csv_kwargs: dict[str, Any] | None = None,
        max_bytes: int | None = None,
        max_rows: int | None = None,
    ) -> ValidationResult:
        """Validate a CSV file (requires ``contractmodel[pandas]``)."""
        validate_limit_params(max_bytes=max_bytes, max_rows=max_rows)
        try:
            file_limit = check_file_byte_limit(path, max_bytes)
            if file_limit is not None:
                return file_limit
            result = dataframe_validation.validate_csv(
                self._ccm,
                path,
                mode=mode,
                read_csv_kwargs=read_csv_kwargs,
                max_rows=max_rows,
            )
        except OptionalDependencyError:
            raise
        except OSError as exc:
            return limit_exceeded_result(f"Failed to read CSV file: {exc}")
        except UnicodeDecodeError as exc:
            return limit_exceeded_result(f"Failed to decode CSV file: {exc}")
        return run_validator_plugins(self._ccm, str(path), result)

    def validate_parquet(
        self,
        path: str | Path,
        *,
        mode: ValidationMode = ValidationMode.STRICT,
        read_parquet_kwargs: dict[str, Any] | None = None,
        max_bytes: int | None = None,
        max_rows: int | None = None,
    ) -> ValidationResult:
        """Validate a Parquet file (requires ``contractmodel[parquet]``)."""
        validate_limit_params(max_bytes=max_bytes, max_rows=max_rows)
        try:
            file_limit = check_file_byte_limit(path, max_bytes)
            if file_limit is not None:
                return file_limit
            result = dataframe_validation.validate_parquet(
                self._ccm,
                path,
                mode=mode,
                read_parquet_kwargs=read_parquet_kwargs,
                max_rows=max_rows,
            )
        except OptionalDependencyError:
            raise
        except OSError as exc:
            return limit_exceeded_result(f"Failed to read Parquet file: {exc}")
        return run_validator_plugins(self._ccm, str(path), result)

    def validate_pandas(
        self,
        df: Any,
        *,
        mode: ValidationMode = ValidationMode.STRICT,
        max_rows: int | None = None,
    ) -> ValidationResult:
        """Validate a Pandas DataFrame (requires ``contractmodel[pandas]``)."""
        result = dataframe_validation.validate_pandas(
            self._ccm,
            df,
            mode=mode,
            max_rows=max_rows,
        )
        return run_validator_plugins(self._ccm, df, result)

    def validate_polars(
        self,
        df: Any,
        *,
        mode: ValidationMode = ValidationMode.STRICT,
        max_rows: int | None = None,
    ) -> ValidationResult:
        """Validate a Polars DataFrame (requires ``contractmodel[polars]``)."""
        result = dataframe_validation.validate_polars(
            self._ccm,
            df,
            mode=mode,
            max_rows=max_rows,
        )
        return run_validator_plugins(self._ccm, df, result)

    def diff(
        self,
        other: DataContract,
        *,
        mode: CompatibilityMode = CompatibilityMode.BACKWARD,
    ) -> ContractDiff:
        """Compare this (old/source) contract to ``other`` (new/target).

        Returns a :class:`~contractmodel.diff.engine.ContractDiff` with
        ``source_version`` from ``self`` and ``target_version`` from ``other``.
        """
        return diff_contracts(self._ccm, other._ccm, mode=mode)

    def diff_odcs(self, other: DataContract) -> dict[str, Any]:
        """Compare ODCS exports with pyodcs compatibility analysis.

        Separate from :meth:`diff`, which operates on the Canonical Contract Model.
        """
        return diff_odcs_documents(self.to_odcs(), other.to_odcs())

    def has_breaking_changes(
        self,
        other: DataContract,
        *,
        mode: CompatibilityMode = CompatibilityMode.BACKWARD,
    ) -> bool:
        """Return whether ``other`` introduces breaking changes relative to ``self``."""
        return self.diff(other, mode=mode).is_breaking

    def is_breaking_change(
        self,
        other: DataContract,
        *,
        mode: CompatibilityMode = CompatibilityMode.BACKWARD,
    ) -> bool:
        """Alias for :meth:`has_breaking_changes` (deprecated name, kept for compatibility)."""
        return self.has_breaking_changes(other, mode=mode)

    def to_yaml(self, path: str | Path | None = None) -> str:
        """Serialize the CCM to YAML (``schema`` alias preserved). Optionally write to ``path``."""
        content = yaml.safe_dump(
            self._ccm.model_dump(mode="json", by_alias=True),
            sort_keys=False,
        )
        if path is not None:
            Path(path).write_text(content, encoding="utf-8")
        return content

    def to_json(self, path: str | Path | None = None, *, indent: int = 2) -> str:
        """Serialize the CCM to JSON. Optionally write to ``path``."""
        content = self._ccm.model_dump_json(by_alias=True, indent=indent)
        if path is not None:
            Path(path).write_text(content, encoding="utf-8")
        return content

    def save(
        self,
        path: str | Path,
        *,
        format: Literal["auto", "ccm", "odcs"] = "auto",
    ) -> None:
        """Write the contract to disk in CCM (YAML/JSON) or ODCS YAML format."""
        target = Path(path)
        resolved = format
        if resolved == "auto":
            resolved = "odcs" if _looks_like_odcs_path(target) else "ccm"
        if resolved == "odcs":
            content = yaml.safe_dump(self.to_odcs(), sort_keys=False)
            target.write_text(content, encoding="utf-8")
        elif resolved == "ccm":
            if target.suffix.lower() == ".json":
                self.to_json(target)
            else:
                self.to_yaml(target)
        else:
            msg = f"Unsupported format: {format}"
            raise ValueError(msg)

    def to_odcs(self) -> dict[str, Any]:
        """Export as an ODCS document dict."""
        return export_odcs(self._ccm)

    def to_json_schema(self) -> dict[str, Any]:
        """Export as a JSON Schema dict."""
        return export_json_schema(self._ccm)

    def to_openapi(self) -> dict[str, Any]:
        """Export as a minimal OpenAPI 3.1 document (info + components/schemas)."""
        return export_openapi(self._ccm)

    def to_markdown(self) -> str:
        """Export as human-readable Markdown."""
        return export_markdown(self._ccm)

    def to_rdf(self) -> str:
        """Export as RDF Turtle (requires ``contractmodel[semantic]``)."""
        return export_rdf(self._ccm)

    def to_shacl(self) -> str:
        """Export as SHACL shapes (requires ``contractmodel[semantic]``)."""
        return export_shacl(self._ccm)

    def to_owl(self) -> str:
        """Export as OWL (requires ``contractmodel[semantic]``)."""
        return export_owl(self._ccm)
