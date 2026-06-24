"""Bundled and repository example contract helpers."""

from __future__ import annotations

import importlib.resources
import json
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from contractmodel.adapters.odcs import is_odcs_document
from contractmodel.contract import DataContract
from contractmodel.core.ccm import CanonicalContract


def _dev_examples_dir() -> Path:
    return Path(__file__).resolve().parent.parent.parent / "examples"


def _validate_example_name(name: str) -> None:
    """Reject paths that escape the examples bundle or repository directory."""
    if not name or name.startswith("/") or name.startswith("\\"):
        msg = f"Invalid example name: {name!r}"
        raise ValueError(msg)
    path = Path(name)
    if path.is_absolute():
        msg = f"Invalid example name: {name!r}"
        raise ValueError(msg)
    if ".." in path.parts:
        msg = f"Invalid example name: {name!r}"
        raise ValueError(msg)


def _assert_within_root(path: Path, root: Path) -> None:
    resolved = path.resolve()
    root_resolved = root.resolve()
    if not resolved.is_relative_to(root_resolved):
        msg = f"Example path escapes allowed directory: {path}"
        raise ValueError(msg)


def _bundled_file(name: str) -> Any:
    _validate_example_name(name)
    root = importlib.resources.files("contractmodel").joinpath("examples_data")
    ref: Any = root
    for part in Path(name).parts:
        ref = ref.joinpath(part)
    return ref


def read_example_text(name: str) -> str:
    """Read example file contents from the repo checkout or installed package."""
    _validate_example_name(name)
    dev_root = _dev_examples_dir()
    dev_path = dev_root / name
    if dev_path.is_file():
        _assert_within_root(dev_path, dev_root)
        return dev_path.read_text(encoding="utf-8")
    return str(_bundled_file(name).read_text(encoding="utf-8"))


@lru_cache(maxsize=32)
def example_path(name: str) -> Path:
    """Return a filesystem path to an example file.

    Uses the repository ``examples/`` directory when developing from a clone.
    When installed from PyPI, extracts bundled examples to a stable cache path.
    """
    _validate_example_name(name)
    dev_root = _dev_examples_dir()
    dev_path = dev_root / name
    if dev_path.is_file():
        _assert_within_root(dev_path, dev_root)
        return dev_path

    cache_root = Path.home() / ".cache" / "contractmodel" / "examples"
    cached = (cache_root / name).resolve()
    _assert_within_root(cached, cache_root.resolve())
    if not cached.is_file():
        cached.parent.mkdir(parents=True, exist_ok=True)
        cached.write_bytes(_bundled_file(name).read_bytes())
    return cached


def list_examples() -> list[str]:
    """List bundled example contract and data filenames."""
    return [
        "customer_events.ccm.yaml",
        "customer_events.odcs.yaml",
        "nested_schema.ccm.yaml",
        "data/customer_event.json",
        "data/events.csv",
    ]


def load_example(name: str) -> DataContract:
    """Load a bundled example contract as a :class:`DataContract`."""
    if name.startswith("data/"):
        msg = f"{name!r} is sample data, not a contract. Use example_path() for file paths."
        raise ValueError(msg)

    text = read_example_text(name)
    if name.endswith(".json"):
        data: dict[str, Any] = json.loads(text)
    else:
        loaded = yaml.safe_load(text)
        if not isinstance(loaded, dict):
            msg = f"Example {name!r} must contain a mapping"
            raise ValueError(msg)
        data = loaded

    if is_odcs_document(data):
        return DataContract.from_odcs_dict(data)
    return DataContract(CanonicalContract.model_validate(data))
