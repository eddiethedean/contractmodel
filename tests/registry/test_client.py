"""Tests for registry client."""

import json
import urllib.error
from unittest.mock import MagicMock, patch

import pytest

from contractmodel.core.ccm import CanonicalContract
from contractmodel.errors import RegistryError
from contractmodel.registry.client import fetch_contract, get_registry_url, publish_contract


def _sample_contract() -> CanonicalContract:
    return CanonicalContract.model_validate(
        {
            "contract_id": "test",
            "name": "Test",
            "version": "1.0.0",
            "schema": {"fields": [{"name": "id", "logical_type": "string"}]},
        }
    )


def test_get_registry_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CONTRACT_REGISTRY_URL", raising=False)
    assert get_registry_url() is None
    monkeypatch.setenv("CONTRACT_REGISTRY_URL", "http://registry.test")
    assert get_registry_url() == "http://registry.test"


def test_publish_contract_success() -> None:
    contract = _sample_contract()
    captured: list[object] = []
    response = MagicMock()
    response.status = 201
    response.__enter__ = lambda self: self
    response.__exit__ = MagicMock(return_value=False)

    def fake_urlopen(request: object, timeout: int = 30) -> MagicMock:
        captured.append(request)
        return response

    with patch("urllib.request.urlopen", side_effect=fake_urlopen):
        result = publish_contract(contract, "http://registry.test/")
    assert result.status == "201"
    assert result.contract_id == "test"
    request = captured[0]
    assert request.full_url == "http://registry.test/contracts/test/versions"
    assert request.method == "POST"
    assert request.headers["Content-type"] == "application/json"
    payload = json.loads(request.data.decode())
    assert payload["contract_id"] == "test"


def test_publish_contract_sends_auth_header(monkeypatch: pytest.MonkeyPatch) -> None:
    contract = _sample_contract()
    captured: list[object] = []
    response = MagicMock()
    response.status = 201
    response.__enter__ = lambda self: self
    response.__exit__ = MagicMock(return_value=False)
    monkeypatch.setenv("CONTRACT_REGISTRY_TOKEN", "secret-token")

    def fake_urlopen(request: object, timeout: int = 30) -> MagicMock:
        captured.append(request)
        return response

    with patch("urllib.request.urlopen", side_effect=fake_urlopen):
        publish_contract(contract, "http://registry.test")
    request = captured[0]
    assert request.headers["Authorization"] == "Bearer secret-token"


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
    captured: list[str] = []
    response = MagicMock()
    response.read.return_value = json.dumps(payload).encode()
    response.__enter__ = lambda self: self
    response.__exit__ = MagicMock(return_value=False)

    def fake_urlopen(request: object, timeout: int = 30) -> MagicMock:
        url = getattr(request, "full_url", request)
        captured.append(str(url))
        return response

    with patch("urllib.request.urlopen", side_effect=fake_urlopen):
        contract = fetch_contract("http://registry.test/", "test", version="1.0.0")
    assert contract.contract_id == "test"
    assert captured[0] == "http://registry.test/contracts/test/versions/1.0.0"


def test_fetch_contract_without_version_uses_base_path() -> None:
    payload = {
        "contract_id": "test",
        "name": "Test",
        "version": "1.0.0",
        "schema": {"fields": [{"name": "id", "logical_type": "string"}]},
    }
    captured: list[str] = []
    response = MagicMock()
    response.read.return_value = json.dumps(payload).encode()
    response.__enter__ = lambda self: self
    response.__exit__ = MagicMock(return_value=False)

    def fake_urlopen(request: object, timeout: int = 30) -> MagicMock:
        url = getattr(request, "full_url", request)
        captured.append(str(url))
        return response

    with patch("urllib.request.urlopen", side_effect=fake_urlopen):
        fetch_contract("http://registry.test", "test")
    assert captured[0] == "http://registry.test/contracts/test"


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
