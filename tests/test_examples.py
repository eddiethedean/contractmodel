"""Tests for bundled example helpers."""

from pathlib import Path

import pytest

import contractmodel.examples as examples_mod
from contractmodel.examples import example_path, list_examples, load_example, read_example_text


def test_list_examples() -> None:
    names = list_examples()
    assert "customer_events.odcs.yaml" in names
    assert "data/customer_event.json" in names


def test_load_example_odcs() -> None:
    contract = load_example("customer_events.odcs.yaml")
    assert contract.ccm.contract_id == "customer-events"


def test_load_example_ccm() -> None:
    contract = load_example("customer_events.ccm.yaml")
    assert contract.ccm.contract_id == "customer-events"


def test_load_example_nested_schema() -> None:
    contract = load_example("nested_schema.ccm.yaml")
    assert contract.ccm.contract_id == "nested-example"


def test_load_example_rejects_data_file() -> None:
    with pytest.raises(ValueError, match="sample data"):
        load_example("data/customer_event.json")


def test_example_path_exists() -> None:
    path = example_path("customer_events.odcs.yaml")
    assert path.is_file()


def test_read_example_text() -> None:
    text = read_example_text("customer_events.odcs.yaml")
    assert "customer-events" in text


def test_read_example_text_data_file() -> None:
    text = read_example_text("data/customer_event.json")
    assert "event_id" in text


def test_example_path_dev_clone() -> None:
    dev = Path(__file__).resolve().parents[1] / "examples" / "customer_events.odcs.yaml"
    assert dev.is_file()
    assert example_path("customer_events.odcs.yaml") == dev


def test_example_path_bundled_cache(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(examples_mod, "_dev_examples_dir", lambda: tmp_path / "missing")
    examples_mod.example_path.cache_clear()
    cached = example_path("customer_events.odcs.yaml")
    assert cached.is_file()
    assert cached == example_path("customer_events.odcs.yaml")
    examples_mod.example_path.cache_clear()


def test_read_example_text_bundled(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(examples_mod, "_dev_examples_dir", lambda: tmp_path / "missing")
    text = read_example_text("customer_events.odcs.yaml")
    assert "customer-events" in text


def test_load_example_invalid_yaml(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(examples_mod, "_dev_examples_dir", lambda: tmp_path)
    bad = tmp_path / "bad.ccm.yaml"
    bad.write_text("not-a-mapping\n", encoding="utf-8")
    with pytest.raises(ValueError, match="mapping"):
        load_example("bad.ccm.yaml")


def test_load_example_json_contract(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = (
        '{"contract_id": "json-example", "name": "JSON", "version": "1.0.0", '
        '"schema": {"fields": [{"name": "id", "logical_type": "string"}]}}'
    )
    monkeypatch.setattr(examples_mod, "read_example_text", lambda _name: payload)
    contract = load_example("sample.ccm.json")
    assert contract.ccm.contract_id == "json-example"


def test_examples_dirs_stay_in_sync() -> None:
    repo_examples = Path(__file__).resolve().parents[1] / "examples"
    bundled = Path(__file__).resolve().parents[1] / "src" / "contractmodel" / "examples_data"

    def relative_files(root: Path) -> set[str]:
        return {
            str(path.relative_to(root))
            for path in root.rglob("*")
            if path.is_file() and path.name != "README.md"
        }

    assert relative_files(repo_examples) == relative_files(bundled)
