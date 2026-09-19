"""Async client for Monitor Suite Agent."""

from __future__ import annotations

from dataclasses import dataclass
from json import JSONDecodeError
from typing import Any

from aiohttp import ClientError, ClientResponseError, ClientSession, ClientTimeout
from yarl import URL

from .const import REQUEST_TIMEOUT_SECONDS


class MonitorSuiteError(Exception):
    """Base Monitor Suite API error."""


class MonitorSuiteAuthenticationError(MonitorSuiteError):
    """The API token was rejected."""


class MonitorSuiteConnectionError(MonitorSuiteError):
    """The agent could not be reached."""


class MonitorSuiteInvalidResponseError(MonitorSuiteError):
    """The endpoint did not return the expected contract."""


class MonitorSuiteNotReadyError(MonitorSuiteError):
    """The agent has not produced a status sample yet."""


@dataclass(frozen=True, slots=True)
class MonitorSuiteHealth:
    """Validated health response."""

    status: str
    version: str
    sample_available: bool


@dataclass(frozen=True, slots=True)
class MonitorSuiteConnectionInfo:
    """Validated connection details returned by setup flows."""

    host: str
    port: int
    health: MonitorSuiteHealth
    status: dict[str, Any]


def normalize_host(host: str) -> str:
    """Normalize a hostname or IP address for storage and comparison."""
    normalized = URL.build(scheme="http", host=host.strip()).host
    if not normalized:
        raise ValueError("Host is required")
    return normalized.lower()


def endpoint_id(host: str, port: int) -> str:
    """Build the stable endpoint identifier used by config entries."""
    normalized = normalize_host(host)
    return str(URL.build(scheme="http", host=normalized, port=port).with_path(""))


class MonitorSuiteClient:
    """Client using Home Assistant's shared aiohttp session."""

    def __init__(
        self, session: ClientSession, host: str, port: int, api_key: str
    ) -> None:
        self._session = session
        self._base_url = URL.build(scheme="http", host=normalize_host(host), port=port)
        self._headers = {"X-API-Key": api_key}
        self._timeout = ClientTimeout(total=REQUEST_TIMEOUT_SECONDS)

    async def _get_json(self, path: str) -> dict[str, Any]:
        try:
            async with self._session.get(
                self._base_url.with_path(path),
                headers=self._headers,
                allow_redirects=False,
                timeout=self._timeout,
            ) as response:
                if response.status in (401, 403):
                    raise MonitorSuiteAuthenticationError("API token was rejected")
                if 300 <= response.status < 400:
                    raise MonitorSuiteInvalidResponseError("Unexpected redirect")
                if response.status == 503:
                    raise MonitorSuiteNotReadyError(
                        "Status sample is not available yet"
                    )
                response.raise_for_status()
                try:
                    payload = await response.json(content_type=None)
                except (JSONDecodeError, ValueError) as err:
                    raise MonitorSuiteInvalidResponseError(
                        "Response is not valid JSON"
                    ) from err
        except (
            MonitorSuiteAuthenticationError,
            MonitorSuiteInvalidResponseError,
            MonitorSuiteNotReadyError,
        ):
            raise
        except ClientResponseError as err:
            raise MonitorSuiteInvalidResponseError(
                f"Unexpected HTTP status {err.status}"
            ) from err
        except (ClientError, TimeoutError) as err:
            raise MonitorSuiteConnectionError(str(err)) from err

        if not isinstance(payload, dict):
            raise MonitorSuiteInvalidResponseError("Response is not a JSON object")
        return payload

    async def async_health(self) -> MonitorSuiteHealth:
        """Read and validate the health contract."""
        payload = await self._get_json("/health")
        status = payload.get("status")
        version = payload.get("version")
        sample_available = payload.get("sample_available")
        if status not in {"starting", "ok", "degraded", "stale"}:
            raise MonitorSuiteInvalidResponseError("Unexpected health status")
        if not isinstance(version, str) or not version:
            raise MonitorSuiteInvalidResponseError("Missing agent version")
        if not isinstance(sample_available, bool):
            raise MonitorSuiteInvalidResponseError("Missing sample availability")
        return MonitorSuiteHealth(status, version, sample_available)

    async def async_status(self) -> dict[str, Any]:
        """Read and validate one complete status snapshot."""
        payload = await self._get_json("/status")
        required_objects = {
            "device",
            "cpu",
            "memory",
            "root_filesystem",
            "power",
            "cooling",
            "network",
            "disk_activity",
            "system",
            "raid",
            "smart",
            "health",
        }
        if not isinstance(payload.get("updated_at"), str):
            raise MonitorSuiteInvalidResponseError("Missing update timestamp")
        if any(not isinstance(payload.get(key), dict) for key in required_objects):
            raise MonitorSuiteInvalidResponseError("Incomplete status response")
        if not isinstance(payload["raid"].get("arrays"), list):
            raise MonitorSuiteInvalidResponseError("Invalid RAID data")
        if not isinstance(payload["smart"].get("devices"), list):
            raise MonitorSuiteInvalidResponseError("Invalid SMART data")
        return payload


async def async_validate_connection(
    session: ClientSession, host: str, port: int, api_key: str
) -> MonitorSuiteConnectionInfo:
    """Validate one complete agent connection for a setup flow."""
    normalized_host = normalize_host(host)
    client = MonitorSuiteClient(session, normalized_host, port, api_key)
    health = await client.async_health()
    if not health.sample_available:
        raise MonitorSuiteNotReadyError("Status sample is not available yet")
    status = await client.async_status()
    return MonitorSuiteConnectionInfo(normalized_host, port, health, status)
