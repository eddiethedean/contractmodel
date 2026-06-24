"""Tests for DataFrame validation."""

from pathlib import Path

import pytest

from contractmodel import DataContract
from contractmodel.core.ccm import CanonicalContract
from contractmodel.errors import OptionalDependencyError

EXAMPLES_DIR = Path(__file__).resolve().parents[2] / "examples"

pd = pytest.importorskip("pandas")


def _contract() -> DataContract:
    return DataContract.from_odcs(EXAMPLES_DIR / "customer_events.odcs.yaml")


def test_validate_pandas_success() -> None:
    df = pd.DataFrame(
        [
            {
                "event_id": "550e8400-e29b-41d4-a716-446655440000",
                "customer_id": "C123",
                "event_timestamp": "2026-06-23T12:00:00",
                "event_type": "created",
            }
        ]
    )
    result = _contract().validate_pandas(df)
    assert result.success is True


def test_validate_pandas_missing_column() -> None:
    df = pd.DataFrame([{"event_id": "550e8400-e29b-41d4-a716-446655440000"}])
    result = _contract().validate_pandas(df)
    assert result.success is False
    assert any(error.code == "CM_SCHEMA_MISSING_FIELD" for error in result.errors)


def test_validate_csv(tmp_path: Path) -> None:
    csv_path = tmp_path / "events.csv"
    pd.DataFrame(
        [
            {
                "event_id": "550e8400-e29b-41d4-a716-446655440000",
                "customer_id": "C123",
                "event_timestamp": "2026-06-23T12:00:00",
                "event_type": "created",
            }
        ]
    ).to_csv(csv_path, index=False)

    result = _contract().validate_csv(csv_path)
    assert result.success is True


@pytest.mark.skipif(
    not pytest.importorskip("pyarrow", reason="pyarrow not installed"),
    reason="pyarrow not installed",
)
def test_validate_parquet(tmp_path: Path) -> None:
    parquet_path = tmp_path / "events.parquet"
    pd.DataFrame(
        [
            {
                "event_id": "550e8400-e29b-41d4-a716-446655440000",
                "customer_id": "C123",
                "event_timestamp": "2026-06-23T12:00:00",
                "event_type": "created",
            }
        ]
    ).to_parquet(parquet_path, index=False)

    result = _contract().validate_parquet(parquet_path)
    assert result.success is True


def test_optional_dependency_error(monkeypatch: pytest.MonkeyPatch) -> None:
    contract = CanonicalContract.model_validate(
        {
            "contract_id": "x",
            "name": "X",
            "version": "1.0.0",
            "schema": {"fields": [{"name": "id", "logical_type": "string"}]},
        }
    )
    wrapper = DataContract.from_ccm(contract)

    def _raise_optional(*_args: object, **_kwargs: object) -> None:
        raise OptionalDependencyError("pandas")

    monkeypatch.setattr(
        "contractmodel.validation.dataframe._import_pandas",
        _raise_optional,
    )
    with pytest.raises(OptionalDependencyError):
        wrapper.validate_csv("dummy.csv")
