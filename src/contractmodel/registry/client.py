"""Registry client for ContractHub-compatible HTTP APIs."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any

from contractmodel.core.ccm import CanonicalContract
from contractmodel.errors import RegistryError

MAX_REGISTRY_RESPONSE_BYTES = 10 * 1024 * 1024


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


def _contract_path_segment(contract_id: str) -> str:
    return urllib.parse.quote(contract_id, safe="")


def _read_bounded_response(response: Any, max_bytes: int = MAX_REGISTRY_RESPONSE_BYTES) -> bytes:
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = response.read(min(65536, max_bytes - total + 1))
        if not isinstance(chunk, (bytes, bytearray)) or len(chunk) == 0:
            break
        total += len(chunk)
        if total > max_bytes:
            msg = f"Registry response exceeds limit of {max_bytes} bytes"
            raise RegistryError(msg)
        chunks.append(bytes(chunk))
    return b"".join(chunks)


def publish_contract(contract: CanonicalContract, registry_url: str) -> RegistryPublishResult:
    """Publish a contract version to a ContractHub-compatible registry."""
    payload = json.dumps(contract.model_dump(mode="json", by_alias=True)).encode()
    contract_segment = _contract_path_segment(contract.contract_id)
    url = f"{registry_url.rstrip('/')}/contracts/{contract_segment}/versions"
    request = urllib.request.Request(
        url,
        data=payload,
        headers=_request_headers(),
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            status = str(response.status)
    except urllib.error.HTTPError as exc:
        raise RegistryError(f"Registry rejected publish with status {exc.code}") from exc
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
    contract_segment = _contract_path_segment(contract_id)
    path = f"{registry_url.rstrip('/')}/contracts/{contract_segment}"
    if version:
        version_segment = _contract_path_segment(version)
        path = f"{path}/versions/{version_segment}"
    request = urllib.request.Request(path, headers=_request_headers(), method="GET")
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            raw = _read_bounded_response(response)
            data: dict[str, Any] = json.loads(raw.decode())
    except RegistryError:
        raise
    except urllib.error.HTTPError as exc:
        raise RegistryError(f"Registry fetch failed with status {exc.code}") from exc
    except urllib.error.URLError as exc:
        raise RegistryError(f"Failed to fetch contract: {exc}") from exc

    if "schema" in data and isinstance(data["schema"], list):
        from contractmodel.adapters.odcs import import_odcs

        return import_odcs(data)
    return CanonicalContract.model_validate(data)
