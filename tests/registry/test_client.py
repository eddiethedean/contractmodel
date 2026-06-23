"""Tests for registry client."""

import json
import urllib.error
from unittest.mock import MagicMock, patch

import pytest

from contractmodel.core.ccm import CanonicalContract
from contractmodel.errors import RegistryError
from contractmodel.registry.client import fetch_contract, get_registry_url, publish_contract


def test_get_registry_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CONTRACT_REGISTRY_URL", raising=False)
    assert get_registry_url() is None
    monkeypatch.setenv("CONTRACT_REGISTRY_URL", "http://registry.test")
    assert get_registry_url() == "http://registry.test"


def test_publish_contract_success() -> None:
    contract = CanonicalContract.model_validate(
        {
            "contract_id": "test",
            "name": "Test",
            "version": "1.0.0",
            "schema": {"fields": [{"name": "id", "logical_type": "string"}]},
        }
    )
    response = MagicMock()
    response.status = 201
    response.__enter__ = lambda self: self
    response.__exit__ = MagicMock(return_value=False)

    with patch("urllib.request.urlopen", return_value=response):
        result = publish_contract(contract, "http://registry.test")
    assert result.status == "201"
    assert result.contract_id == "test"


def test_publish_contract_failure() -> None:
    contract = CanonicalContract.model_validate(
        {
            "contract_id": "test",
            "name": "Test",
            "version": "1.0.0",
            "schema": {"fields": []},
        }
    )
    with (
        patch("urllib.request.urlopen", side_effect=urllib.error.URLError("network")),
        pytest.raises(RegistryError),
    ):
        publish_contract(contract, "http://registry.test")


def test_fetch_contract_ccm() -> None:
    payload = {
        "contract_id": "test",
        "name": "Test",
        "version": "1.0.0",
        "schema": {"fields": [{"name": "id", "logical_type": "string"}]},
    }
    response = MagicMock()
    response.read.return_value = json.dumps(payload).encode()
    response.__enter__ = lambda self: self
    response.__exit__ = MagicMock(return_value=False)

    with patch("urllib.request.urlopen", return_value=response):
        contract = fetch_contract("http://registry.test", "test", version="1.0.0")
    assert contract.contract_id == "test"


def test_fetch_contract_odcs() -> None:
    payload = {
        "apiVersion": "v3.0.0",
        "kind": "DataContract",
        "id": "test",
        "name": "Test",
        "version": "1.0.0",
        "schema": [{"name": "id", "logicalType": "string", "required": True}],
    }
    response = MagicMock()
    response.read.return_value = json.dumps(payload).encode()
    response.__enter__ = lambda self: self
    response.__exit__ = MagicMock(return_value=False)

    with patch("urllib.request.urlopen", return_value=response):
        contract = fetch_contract("http://registry.test", "test")
    assert contract.contract_id == "test"


def test_fetch_contract_failure() -> None:
    with (
        patch("urllib.request.urlopen", side_effect=urllib.error.URLError("network")),
        pytest.raises(RegistryError),
    ):
        fetch_contract("http://registry.test", "missing")
