"""Public bounded loading policy for contract documents."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_serializer

from contractmodel.errors import ContractModelError
from contractmodel.versions import SUPPORTED_ODCS_VERSIONS, is_supported_odcs_version

ContentFormat = Literal["ccm", "odcs"]
EncodingName = Literal["json", "yaml"]


class LoadingPolicyError(ContractModelError):
    """Raised when a contract document violates the loading policy."""


class LoadingPolicy(BaseModel):
    """Bounds and gates applied when loading contract documents (not row data)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    approved_roots: tuple[Path, ...] | None = None
    max_bytes: int | None = 1_048_576
    max_depth: int | None = 64
    max_collection_size: int | None = 10_000
    # Content formats (CCM vs ODCS), not file encodings.
    allowed_formats: frozenset[str] | None = frozenset({"ccm", "odcs"})
    # File encodings accepted by path-based loaders.
    allowed_encodings: frozenset[str] | None = frozenset({"yaml", "json"})
    allowed_odcs_versions: frozenset[str] | None = Field(
        default_factory=lambda: frozenset(SUPPORTED_ODCS_VERSIONS)
    )
    follow_symlinks: bool = False
    require_odcs_version: bool = False

    @field_serializer("allowed_formats", "allowed_encodings", "allowed_odcs_versions")
    def _serialize_sorted_sets(self, value: frozenset[str] | None) -> list[str] | None:
        if value is None:
            return None
        return sorted(value)


DEFAULT_LOADING_POLICY = LoadingPolicy()

# Darwin (and similar) expose /tmp,/var as convenience symlinks into /private/*.
# Those are not attacker-controlled path escapes for LoadingPolicy purposes.
_BENIGN_OS_SYMLINKS = frozenset({"/tmp", "/var", "/etc"})


def _is_benign_os_symlink(path: Path) -> bool:
    """Return True for platform mount aliases such as ``/tmp`` → ``/private/tmp``."""
    if not path.is_symlink():
        return False
    try:
        posix = path.as_posix()
        if posix not in _BENIGN_OS_SYMLINKS:
            return False
        resolved = path.resolve(strict=False).as_posix()
    except OSError:
        return False
    return resolved.startswith("/private/") and resolved.rstrip("/").endswith(path.name)


def _path_has_symlink(path: Path) -> bool:
    """Return True if ``path`` or any non-benign ancestor component is a symlink."""
    current = path
    while True:
        if current.is_symlink() and not _is_benign_os_symlink(current):
            return True
        parent = current.parent
        if parent == current:
            return False
        current = parent


def resolve_contract_path(
    path: str | Path,
    policy: LoadingPolicy | None = None,
) -> Path:
    """Resolve and authorize a contract file path under the loading policy."""
    active = policy or DEFAULT_LOADING_POLICY
    candidate = Path(path)

    if not active.follow_symlinks and _path_has_symlink(candidate.absolute()):
        msg = f"Symlink contract paths are not allowed: {candidate}"
        raise LoadingPolicyError(msg)

    resolved = candidate.resolve(strict=False)
    if active.approved_roots is not None:
        allowed = False
        for root in active.approved_roots:
            root_resolved = root.resolve(strict=False)
            try:
                resolved.relative_to(root_resolved)
                allowed = True
                break
            except ValueError:
                continue
        if not allowed:
            msg = f"Contract path is outside approved_roots: {resolved}"
            raise LoadingPolicyError(msg)

    if not resolved.is_file():
        msg = f"Contract path is not a file: {resolved}"
        raise LoadingPolicyError(msg)

    if active.max_bytes is not None:
        size = resolved.stat().st_size
        if size > active.max_bytes:
            msg = f"Contract file exceeds max_bytes={active.max_bytes} ({size} bytes)"
            raise LoadingPolicyError(msg)

    encoding = "json" if resolved.suffix.lower() == ".json" else "yaml"
    if active.allowed_encodings is not None and encoding not in active.allowed_encodings:
        msg = f"Contract encoding {encoding!r} is not allowed by loading policy"
        raise LoadingPolicyError(msg)

    return resolved


def _collection_size(value: Any) -> int:
    """Count mapping/list nodes (structural), not scalar payload bytes."""
    if isinstance(value, Mapping):
        return len(value) + sum(_collection_size(v) for v in value.values())
    if isinstance(value, list):
        return len(value) + sum(_collection_size(v) for v in value)
    return 0


def _depth(value: Any, current: int = 0) -> int:
    if isinstance(value, Mapping):
        if not value:
            return current
        return max(_depth(v, current + 1) for v in value.values())
    if isinstance(value, list):
        if not value:
            return current
        return max(_depth(v, current + 1) for v in value)
    return current


def enforce_document_bounds(
    data: Mapping[str, Any],
    policy: LoadingPolicy | None = None,
    *,
    format_name: ContentFormat | None = None,
    odcs_api_version: str | None = None,
) -> None:
    """Enforce depth/collection/format/version/byte gates on a parsed contract document."""
    active = policy or DEFAULT_LOADING_POLICY

    if (
        format_name is not None
        and active.allowed_formats is not None
        and format_name not in active.allowed_formats
    ):
        msg = f"Contract format {format_name!r} is not allowed by loading policy"
        raise LoadingPolicyError(msg)

    if active.max_bytes is not None:
        encoded = json.dumps(dict(data), default=str, ensure_ascii=False).encode("utf-8")
        if len(encoded) > active.max_bytes:
            msg = f"Contract document exceeds max_bytes={active.max_bytes} ({len(encoded)} bytes)"
            raise LoadingPolicyError(msg)

    if active.max_depth is not None:
        depth = _depth(data)
        if depth > active.max_depth:
            msg = f"Contract document exceeds max_depth={active.max_depth} (depth={depth})"
            raise LoadingPolicyError(msg)

    if active.max_collection_size is not None:
        size = _collection_size(data)
        if size > active.max_collection_size:
            msg = (
                f"Contract document exceeds max_collection_size="
                f"{active.max_collection_size} (size={size})"
            )
            raise LoadingPolicyError(msg)

    # ODCS version gates apply only to ODCS content.
    if format_name == "odcs" and (odcs_api_version is not None or active.require_odcs_version):
        allowed = active.allowed_odcs_versions
        if allowed is None:
            allowed = frozenset(SUPPORTED_ODCS_VERSIONS)
        if odcs_api_version is None and active.require_odcs_version:
            msg = "ODCS apiVersion is required by loading policy"
            raise LoadingPolicyError(msg)
        if odcs_api_version is not None and odcs_api_version not in allowed:
            if not is_supported_odcs_version(odcs_api_version):
                msg = f"Unsupported ODCS apiVersion: {odcs_api_version!r}"
                raise LoadingPolicyError(msg)
            msg = f"ODCS apiVersion {odcs_api_version!r} is not allowed by loading policy"
            raise LoadingPolicyError(msg)
