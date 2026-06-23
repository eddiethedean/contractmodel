"""Tests for semantic import errors."""

import pytest

from contractmodel.core.ccm import CanonicalContract
from contractmodel.errors import OptionalDependencyError
from contractmodel.semantic import owl, rdf, shacl

CONTRACT = CanonicalContract.model_validate(
    {
        "contract_id": "x",
        "name": "X",
        "version": "1.0.0",
        "schema": {"fields": [{"name": "id", "logical_type": "string"}]},
    }
)


def test_rdf_import_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def _raise() -> tuple[object, object, object, object]:
        raise OptionalDependencyError("semantic")

    monkeypatch.setattr(rdf, "_import_rdflib", _raise)
    with pytest.raises(OptionalDependencyError):
        rdf.export_rdf(CONTRACT)


def test_shacl_import_error(monkeypatch: pytest.MonkeyPatch) -> None:
    import builtins

    real_import = builtins.__import__

    def fake_import(name: str, *args: object, **kwargs: object) -> object:
        if name == "rdflib":
            raise ImportError("no rdflib")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    with pytest.raises(OptionalDependencyError):
        shacl.export_shacl(CONTRACT)


def test_owl_import_error(monkeypatch: pytest.MonkeyPatch) -> None:
    import builtins

    real_import = builtins.__import__

    def fake_import(name: str, *args: object, **kwargs: object) -> object:
        if name == "rdflib":
            raise ImportError("no rdflib")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    with pytest.raises(OptionalDependencyError):
        owl.export_owl(CONTRACT)
