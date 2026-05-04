"""Binary sensor entities for the Nedap AEOS Inventory integration."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER
from .coordinator import AeosInventoryCoordinator
from .entity import AeosInventoryEntity


def _truthy(v: Any) -> bool | None:
    if v is None:
        return None
    return str(v).strip().lower() in ("true", "1", "yes", "on", "enabled")


@dataclass(frozen=True, kw_only=True)
class AeosBinaryDescription(BinarySensorEntityDescription):
    value_fn: Callable[[dict[str, Any]], bool | None] = lambda d: None


BINARY_SENSORS: tuple[AeosBinaryDescription, ...] = (
    AeosBinaryDescription(
        key="online",
        translation_key="online",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        # Always True if we got the dict back from the coordinator;
        # availability handles the offline case.
        value_fn=lambda d: True if d else None,
    ),
    AeosBinaryDescription(
        key="dhcp_enabled",
        translation_key="dhcp_enabled",
        value_fn=lambda d: _truthy(d.get("dhcp_enabled")),
    ),
    AeosBinaryDescription(
        key="snmp_agent_enabled",
        translation_key="snmp_agent_enabled",
        entity_registry_enabled_default=False,
        value_fn=lambda d: _truthy(d.get("snmp_agent_enabled")),
    ),
    AeosBinaryDescription(
        key="secure_mode_enabled",
        translation_key="secure_mode_enabled",
        device_class=BinarySensorDeviceClass.LOCK,
        value_fn=lambda d: _truthy(d.get("secure_mode_enabled")),
    ),
    AeosBinaryDescription(
        key="dot1x_enabled",
        translation_key="dot1x_enabled",
        value_fn=lambda d: _truthy(d.get("802.1x_enabled") or d.get("dot1x_enabled")),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: AeosInventoryCoordinator = hass.data[DOMAIN][entry.entry_id]

    # One-time hub heartbeat sensor for the API itself.
    async_add_entities([AeosApiHeartbeat(coordinator, entry)])

    known_keys: set[str] = set()

    @callback
    def _add_new_devices() -> None:
        new_entities: list[BinarySensorEntity] = []
        for device_key in coordinator.data or {}:
            if device_key in known_keys:
                continue
            known_keys.add(device_key)
            for desc in BINARY_SENSORS:
                new_entities.append(AeosBinarySensor(coordinator, device_key, desc))
        if new_entities:
            async_add_entities(new_entities)

    _add_new_devices()
    entry.async_on_unload(coordinator.async_add_listener(_add_new_devices))


class AeosBinarySensor(AeosInventoryEntity, BinarySensorEntity):
    entity_description: AeosBinaryDescription

    def __init__(
        self,
        coordinator: AeosInventoryCoordinator,
        device_key: str,
        description: AeosBinaryDescription,
    ) -> None:
        super().__init__(coordinator, device_key, description.key)
        self.entity_description = description

    @property
    def is_on(self) -> bool | None:
        return self.entity_description.value_fn(self._device)


class AeosApiHeartbeat(CoordinatorEntity[AeosInventoryCoordinator], BinarySensorEntity):
    """Tracks whether the InventoryAPI is reachable.

    Attached to a synthetic 'API' device so the user can see hub-level health
    independently from any individual controller.
    """

    _attr_has_entity_name = True
    _attr_translation_key = "api_connected"
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_entity_registry_enabled_default = True

    def __init__(
        self,
        coordinator: AeosInventoryCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_api_connected"

    @property
    def is_on(self) -> bool:
        # last_update_success flips False on UpdateFailed
        return bool(self.coordinator.last_update_success)

    @property
    def available(self) -> bool:
        # Always available - the whole point is to report up/down.
        return True

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        c = self.coordinator
        return {
            "last_update_success_time": (
                c.last_update_success_time.isoformat()
                if getattr(c, "last_update_success_time", None) else None
            ),
            "device_count": len(c.data) if c.data else 0,
            "consecutive_failures": getattr(c, "_consecutive_failures", 0),
        }

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, f"{self._entry.entry_id}_api")},
            name=f"AEOS Inventory API ({self._entry.title})",
            manufacturer=MANUFACTURER,
            model="InventoryAPI",
            entry_type=DeviceEntryType.SERVICE,
        )
