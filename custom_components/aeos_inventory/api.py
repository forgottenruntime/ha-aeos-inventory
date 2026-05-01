"""Async client for the Nedap AEOS Inventory API."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp

from .const import HEALTH_PATH, INVENTORY_PATH

_LOGGER = logging.getLogger(__name__)


class AeosInventoryAuthError(Exception):
    """API key was rejected."""


class AeosInventoryConnectionError(Exception):
    """Network / HTTP error talking to the API."""


class AeosInventoryClient:
    """Thin async wrapper around the InventoryAPI HTTP endpoints."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        host: str,
        port: int,
        api_key: str,
        *,
        use_ssl: bool = False,
        verify_ssl: bool = True,
        timeout: int = 30,
    ) -> None:
        scheme = "https" if use_ssl else "http"
        self._base = f"{scheme}://{host}:{port}"
        self._headers = {"X-API-Key": api_key, "Accept": "application/json"}
        self._session = session
        self._verify_ssl = verify_ssl
        self._timeout = aiohttp.ClientTimeout(total=timeout)

    async def async_health(self) -> bool:
        """Return True when /healthz responds 200."""
        try:
            async with self._session.get(
                self._base + HEALTH_PATH,
                timeout=self._timeout,
                ssl=self._verify_ssl,
            ) as resp:
                return resp.status == 200
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise AeosInventoryConnectionError(str(err)) from err

    async def async_inventory(self) -> list[dict[str, Any]]:
        """Fetch /aeosws/inventory and normalise the response to a list."""
        try:
            async with self._session.get(
                self._base + INVENTORY_PATH,
                headers=self._headers,
                timeout=self._timeout,
                ssl=self._verify_ssl,
            ) as resp:
                if resp.status in (401, 403):
                    raise AeosInventoryAuthError(
                        f"API rejected the X-API-Key (HTTP {resp.status})"
                    )
                if resp.status >= 400:
                    text = await resp.text()
                    raise AeosInventoryConnectionError(
                        f"HTTP {resp.status}: {text[:200]}"
                    )
                payload = await resp.json(content_type=None)
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise AeosInventoryConnectionError(str(err)) from err

        if isinstance(payload, dict):
            return [payload]
        if isinstance(payload, list):
            return [d for d in payload if isinstance(d, dict)]
        raise AeosInventoryConnectionError(
            f"Unexpected payload type from inventory endpoint: {type(payload).__name__}"
        )
