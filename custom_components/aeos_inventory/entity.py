"""Shared base entity for the AEOS Inventory integration."""
from __future__ import annotations

from typing import Any

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER
from .coordinator import AeosInventoryCoordinator


class AeosInventoryEntity(CoordinatorEntity[AeosInventoryCoordinator]):
    """Base entity bound to one controller (keyed by serial_number/host)."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: AeosInventoryCoordinator,
        device_key: str,
        entity_suffix: str,
    ) -> None:
        super().__init__(coordinator)
        self._device_key = device_key
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{device_key}_{entity_suffix}"

    @property
    def _device(self) -> dict[str, Any]:
        return self.coordinator.data.get(self._device_key, {}) if self.coordinator.data else {}

    @property
    def available(self) -> bool:
        return super().available and self._device_key in (self.coordinator.data or {})

    @property
    def device_info(self) -> DeviceInfo:
        d = self._device
        host = d.get("host_name") or self._device_key
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_key)},
            name=host,
            manufacturer=d.get("manufacturer") or MANUFACTURER,
            model=d.get("model") or d.get("cb_type"),
            sw_version=d.get("aeos_version"),
            hw_version=d.get("production_date"),
            serial_number=d.get("serial_number"),
            configuration_url=(
                f"http://{d.get('ip_address')}" if d.get("ip_address") else None
            ),
        )
