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
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
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
    entities: list[BinarySensorEntity] = []
    for device_key in coordinator.data or {}:
        for desc in BINARY_SENSORS:
            entities.append(AeosBinarySensor(coordinator, device_key, desc))
    async_add_entities(entities)


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
