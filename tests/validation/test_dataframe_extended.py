"""Extended dataframe validation tests."""

import pytest

from contractmodel.core.ccm import CanonicalContract
from contractmodel.errors import OptionalDependencyError
from contractmodel.validation.dataframe import validate_pandas, validate_polars


def _contract() -> CanonicalContract:
    return CanonicalContract.model_validate(
        {
            "contract_id": "df",
            "name": "DF",
            "version": "1.0.0",
            "schema": {
                "fields": [
                    {"name": "id", "logical_type": "string", "required": True},
                    {"name": "value", "logical_type": "integer", "required": False},
                ]
            },
        }
    )


def test_validate_pandas_wrong_type() -> None:
    pytest.importorskip("pandas")
    with pytest.raises(TypeError, match="pandas.DataFrame"):
        validate_pandas(_contract(), [{"id": "1"}])


def test_validate_pandas_extra_column_strict() -> None:
    pd = pytest.importorskip("pandas")
    df = pd.DataFrame([{"id": "1", "extra": "x"}])
    result = validate_pandas(_contract(), df)
    assert result.success is False
    assert any(error.code == "CM_SCHEMA_EXTRA_FIELD" for error in result.errors)


def test_validate_polars_wrong_type() -> None:
    pytest.importorskip("polars")
    with pytest.raises(TypeError, match="polars.DataFrame"):
        validate_polars(_contract(), {"id": "1"})


def test_validate_polars_success() -> None:
    pl = pytest.importorskip("polars")
    df = pl.DataFrame({"id": ["1"], "value": [1]})
    result = validate_polars(_contract(), df)
    assert result.success is True


def test_import_pandas_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    import builtins

    real_import = builtins.__import__

    def fake_import(name: str, *args: object, **kwargs: object) -> object:
        if name == "pandas":
            raise ImportError("no pandas")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    with pytest.raises(OptionalDependencyError):
        validate_pandas(_contract(), object())
