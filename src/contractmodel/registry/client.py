"""Registry client."""

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


def publish_contract(contract: CanonicalContract, registry_url: str) -> RegistryPublishResult:
    """Publish a contract to a registry endpoint."""
    payload = json.dumps(contract.model_dump(mode="json", by_alias=True)).encode()
    request = urllib.request.Request(
        f"{registry_url.rstrip('/')}/contracts",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            status = str(response.status)
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
    """Fetch a contract from a registry endpoint."""
    path = f"{registry_url.rstrip('/')}/contracts/{contract_id}"
    if version:
        path = f"{path}/versions/{version}"
    try:
        with urllib.request.urlopen(path, timeout=30) as response:
            data: dict[str, Any] = json.loads(response.read().decode())
    except urllib.error.URLError as exc:
        raise RegistryError(f"Failed to fetch contract: {exc}") from exc

    if "schema" in data and isinstance(data["schema"], list):
        from contractmodel.adapters.odcs import import_odcs

        return import_odcs(data)
    return CanonicalContract.model_validate(data)
