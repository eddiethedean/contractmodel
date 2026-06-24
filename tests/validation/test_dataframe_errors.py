"""Dataframe validation error-path tests."""

from pathlib import Path

import pytest

from contractmodel import DataContract
from contractmodel.core.ccm import CanonicalContract
from contractmodel.validation import dataframe as dataframe_validation


def _contract() -> CanonicalContract:
    return CanonicalContract.model_validate(
        {
            "contract_id": "x",
            "name": "X",
            "version": "1.0.0",
            "schema": {"fields": [{"name": "id", "logical_type": "string", "required": True}]},
        }
    )


def test_validate_csv_os_error_returns_result(tmp_path: Path) -> None:
    missing = tmp_path / "missing.csv"
    result = dataframe_validation.validate_csv(_contract(), missing)
    assert result.success is False
    assert result.errors[0].code == "CM_RUNTIME_ERROR"


def test_validate_csv_parse_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pd = pytest.importorskip("pandas")
    path = tmp_path / "bad.csv"
    path.write_text("id\n\"unclosed", encoding="utf-8")

    def _broken_read_csv(*_args: object, **_kwargs: object) -> pd.DataFrame:
        raise ValueError("parse failure")

    monkeypatch.setattr(pd, "read_csv", _broken_read_csv)
    result = dataframe_validation.validate_csv(_contract(), path)
    assert result.success is False
    assert "parse" in result.errors[0].message.lower()


def test_validate_polars_via_facade() -> None:
    pl = pytest.importorskip("polars")
    contract = DataContract.from_ccm(_contract())
    df = pl.DataFrame({"id": ["a"]})
    result = contract.validate_polars(df)
    assert result.success is True


def test_validate_parquet_os_error_returns_result(tmp_path: Path) -> None:
    pytest.importorskip("pandas")
    pytest.importorskip("pyarrow")
    missing = tmp_path / "missing.parquet"
    result = dataframe_validation.validate_parquet(_contract(), missing)
    assert result.success is False


def test_validate_json_array_max_rows() -> None:
    contract = CanonicalContract.model_validate(
        {
            "contract_id": "x",
            "name": "X",
            "version": "1.0.0",
            "schema": {"fields": [{"name": "id", "logical_type": "string"}]},
        }
    )
    from contractmodel.validation.engine import validate_json

    result = validate_json(contract, '[{"id": "a"}, {"id": "b"}]', max_rows=1)
    assert result.success is False


def test_validate_pandas_row_limit() -> None:
    pd = pytest.importorskip("pandas")
    df = pd.DataFrame({"id": ["a", "b"]})
    result = dataframe_validation.validate_pandas(_contract(), df, max_rows=1)
    assert result.success is False


def test_validate_polars_row_limit() -> None:
    pl = pytest.importorskip("polars")
    df = pl.DataFrame({"id": ["a", "b"]})
    result = dataframe_validation.validate_polars(_contract(), df, max_rows=1)
    assert result.success is False


def test_fetch_contract_invalid_contract_payload() -> None:
    import json
    from unittest.mock import MagicMock, patch

    from contractmodel.errors import RegistryError
    from contractmodel.registry.client import fetch_contract

    payload = {"not": "a contract"}
    response = MagicMock()
    response.read.side_effect = [json.dumps(payload).encode(), b""]
    response.__enter__ = lambda self: self
    response.__exit__ = MagicMock(return_value=False)
    with (
        patch("urllib.request.urlopen", return_value=response),
        pytest.raises(RegistryError, match="invalid contract"),
    ):
        fetch_contract("http://registry.test", "test")
