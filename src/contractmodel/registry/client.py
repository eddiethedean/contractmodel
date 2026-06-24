"""Registry client for ContractHub-compatible HTTP APIs."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

from contractmodel.core.ccm import CanonicalContract
from contractmodel.errors import RegistryError


@dataclass
class RegistryPublishResult:
    contract_id: str
    version: str
    registry_url: str
    status: str


def get_registry_url() -> str | None:
    """Return configured registry URL from environment."""
    return os.environ.get("CONTRACT_REGISTRY_URL")


def get_registry_token() -> str | None:
    """Return bearer token for registry authentication."""
    return os.environ.get("CONTRACT_REGISTRY_TOKEN")


def _request_headers() -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    token = get_registry_token()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def publish_contract(contract: CanonicalContract, registry_url: str) -> RegistryPublishResult:
    """Publish a contract version to a ContractHub-compatible registry."""
    payload = json.dumps(contract.model_dump(mode="json", by_alias=True)).encode()
    url = f"{registry_url.rstrip('/')}/contracts/{contract.contract_id}/versions"
    request = urllib.request.Request(
        url,
        data=payload,
        headers=_request_headers(),
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            status = str(response.status)
            if response.status >= 400:
                raise RegistryError(f"Registry rejected publish with status {response.status}")
    except urllib.error.URLError as exc:
        raise RegistryError(f"Failed to publish contract: {exc}") from exc

    return RegistryPublishResult(
        contract_id=contract.contract_id,
        version=contract.version,
        registry_url=registry_url,
        status=status,
    )


def fetch_contract(
    registry_url: str,
    contract_id: str,
    version: str | None = None,
) -> CanonicalContract:
    """Fetch a contract from a ContractHub-compatible registry."""
    path = f"{registry_url.rstrip('/')}/contracts/{contract_id}"
    if version:
        path = f"{path}/versions/{version}"
    request = urllib.request.Request(path, headers=_request_headers(), method="GET")
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            data: dict[str, Any] = json.loads(response.read().decode())
    except urllib.error.URLError as exc:
        raise RegistryError(f"Failed to fetch contract: {exc}") from exc

    if "schema" in data and isinstance(data["schema"], list):
        from contractmodel.adapters.odcs import import_odcs

        return import_odcs(data)
    return CanonicalContract.model_validate(data)
