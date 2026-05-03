"""Sensor entities for the Nedap AEOS Inventory integration."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfInformation, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import AeosInventoryCoordinator
from .entity import AeosInventoryEntity


def _kb_free(value: str | None) -> int | None:
    """Parse 'total/free' (KiB) and return free in KiB."""
    if not value or "/" not in value:
        return None
    try:
        return int(value.split("/", 1)[1])
    except (ValueError, IndexError):
        return None


def _kb_total(value: str | None) -> int | None:
    if not value or "/" not in value:
        return None
    try:
        return int(value.split("/", 1)[0])
    except (ValueError, IndexError):
        return None


def _to_int(value: Any) -> int | None:
    try:
        return int(str(value).replace(",", ""))
    except (TypeError, ValueError):
        return None


def _to_datetime(value: Any) -> datetime | None:
    """Parse an ISO-8601 string (with or without trailing Z) into a tz-aware datetime."""
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    s = str(value).strip()
    if not s:
        return None
    # Python <3.11 doesn't accept the trailing 'Z' in fromisoformat.
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(s)
    except ValueError:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


@dataclass(frozen=True, kw_only=True)
class AeosSensorDescription(SensorEntityDescription):
    value_fn: Callable[[dict[str, Any]], Any] = lambda d: None


SENSORS: tuple[AeosSensorDescription, ...] = (
    AeosSensorDescription(
        key="ip_address",
        translation_key="ip_address",
        icon="mdi:ip-network",
        value_fn=lambda d: d.get("ip_address"),
    ),
    AeosSensorDescription(
        key="mac",
        translation_key="mac",
        icon="mdi:network",
        entity_registry_enabled_default=False,
        value_fn=lambda d: d.get("mac"),
    ),
    AeosSensorDescription(
        key="aeos_version",
        translation_key="aeos_version",
        icon="mdi:tag",
        value_fn=lambda d: d.get("aeos_version"),
    ),
    AeosSensorDescription(
        key="firmware_name",
        translation_key="firmware_name",
        icon="mdi:chip",
        value_fn=lambda d: d.get("firmware_name"),
    ),
    AeosSensorDescription(
        key="firmware_version",
        translation_key="firmware_version",
        icon="mdi:numeric",
        value_fn=lambda d: d.get("firmware_version"),
    ),
    AeosSensorDescription(
        key="firmware_date",
        translation_key="firmware_date",
        icon="mdi:calendar",
        value_fn=lambda d: d.get("firmware_date"),
    ),
    AeosSensorDescription(
        key="boot_firmware_version",
        translation_key="boot_firmware_version",
        icon="mdi:chip",
        entity_registry_enabled_default=False,
        value_fn=lambda d: d.get("boot_firmware_version"),
    ),
    AeosSensorDescription(
        key="cb_type",
        translation_key="cb_type",
        icon="mdi:developer-board",
        value_fn=lambda d: d.get("cb_type"),
    ),
    AeosSensorDescription(
        key="model",
        translation_key="model",
        icon="mdi:devices",
        value_fn=lambda d: d.get("model"),
    ),
    AeosSensorDescription(
        key="ntp_server",
        translation_key="ntp_server",
        icon="mdi:clock-outline",
        entity_registry_enabled_default=False,
        value_fn=lambda d: d.get("ntp_server"),
    ),
    AeosSensorDescription(
        key="aeserver_host_name",
        translation_key="aeserver_host_name",
        icon="mdi:server",
        value_fn=lambda d: d.get("aeserver_host_name"),
    ),
    AeosSensorDescription(
        key="memory_free_kb",
        translation_key="memory_free_kb",
        device_class=SensorDeviceClass.DATA_SIZE,
        native_unit_of_measurement=UnitOfInformation.KIBIBYTES,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: _kb_free(d.get("memory_total_free_kb")),
    ),
    AeosSensorDescription(
        key="memory_total_kb",
        translation_key="memory_total_kb",
        device_class=SensorDeviceClass.DATA_SIZE,
        native_unit_of_measurement=UnitOfInformation.KIBIBYTES,
        entity_registry_enabled_default=False,
        value_fn=lambda d: _kb_total(d.get("memory_total_free_kb")),
    ),
    AeosSensorDescription(
        key="disk_free_kb",
        translation_key="disk_free_kb",
        device_class=SensorDeviceClass.DATA_SIZE,
        native_unit_of_measurement=UnitOfInformation.KIBIBYTES,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: _kb_free(d.get("disk_total_free_kb")),
    ),
    AeosSensorDescription(
        key="uptime_seconds",
        translation_key="uptime_seconds",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: _to_int(d.get("uptime_seconds")),
    ),
    AeosSensorDescription(
        key="last_reboot",
        translation_key="last_reboot",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda d: _to_datetime(d.get("last_reboot")),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: AeosInventoryCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[SensorEntity] = []
    for device_key in coordinator.data or {}:
        for desc in SENSORS:
            entities.append(AeosSensor(coordinator, device_key, desc))
    async_add_entities(entities)


class AeosSensor(AeosInventoryEntity, SensorEntity):
    entity_description: AeosSensorDescription

    def __init__(
        self,
        coordinator: AeosInventoryCoordinator,
        device_key: str,
        description: AeosSensorDescription,
    ) -> None:
        super().__init__(coordinator, device_key, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> Any:
        return self.entity_description.value_fn(self._device)
