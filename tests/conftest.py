"""Shared pytest fixtures for ContractModel tests."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from contractmodel import DataContract


@pytest.fixture(scope="session")
def examples_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "examples"


@pytest.fixture
def customer_events_ccm_dict(examples_dir: Path) -> dict:
    return yaml.safe_load((examples_dir / "customer_events.ccm.yaml").read_text())


@pytest.fixture
def customer_events_contract(examples_dir: Path) -> DataContract:
    return DataContract.from_odcs(examples_dir / "customer_events.odcs.yaml")
