"""DataUpdateCoordinator for the Nedap AEOS Inventory integration."""
from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    AeosInventoryAuthError,
    AeosInventoryClient,
    AeosInventoryConnectionError,
)
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class AeosInventoryCoordinator(DataUpdateCoordinator[dict[str, dict[str, Any]]]):
    """Polls the InventoryAPI and exposes results keyed by serial_number/host."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        client: AeosInventoryClient,
        scan_interval: int,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN} ({entry.title})",
            update_interval=timedelta(seconds=scan_interval),
        )
        self._client = client
        self.entry = entry

    async def _async_update_data(self) -> dict[str, dict[str, Any]]:
        try:
            devices = await self._client.async_inventory()
        except AeosInventoryAuthError as err:
            raise UpdateFailed(f"Authentication error: {err}") from err
        except AeosInventoryConnectionError as err:
            raise UpdateFailed(f"Connection error: {err}") from err

        result: dict[str, dict[str, Any]] = {}
        for d in devices:
            key = (
                d.get("serial_number")
                or d.get("host_name")
                or d.get("ip_address")
                or f"unknown-{len(result)}"
            )
            result[str(key).lower()] = d
        return result
