"""Binary sensor entities for Tara Polar Station."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, NAME
from .coordinator import TaraPolarStationCoordinator

ValueFn = Callable[[dict[str, Any]], bool]


@dataclass(frozen=True, kw_only=True)
class TaraBinarySensorDescription(BinarySensorEntityDescription):
    """Description for Tara binary sensors."""

    value_fn: ValueFn


BINARY_SENSOR_TYPES: tuple[TaraBinarySensorDescription, ...] = (
    TaraBinarySensorDescription(
        key="in_arctic_circle",
        translation_key="in_arctic_circle",
        value_fn=lambda data: bool(data.get("in_arctic_circle")),
        icon="mdi:snowflake-variant",
    ),
    TaraBinarySensorDescription(
        key="in_polar_day",
        translation_key="in_polar_day",
        value_fn=lambda data: bool(data.get("in_polar_day")),
        icon="mdi:white-balance-sunny",
    ),
    TaraBinarySensorDescription(
        key="in_polar_night",
        translation_key="in_polar_night",
        value_fn=lambda data: bool(data.get("in_polar_night")),
        icon="mdi:weather-night",
    ),
    TaraBinarySensorDescription(
        key="stationary",
        translation_key="stationary",
        value_fn=lambda data: bool(data.get("stationary")),
        icon="mdi:ship-wheel",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Tara binary sensors."""
    coordinator: TaraPolarStationCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        TaraBinarySensorEntity(coordinator, description, entry.entry_id)
        for description in BINARY_SENSOR_TYPES
    )


class TaraBinarySensorEntity(
    CoordinatorEntity[TaraPolarStationCoordinator], BinarySensorEntity
):
    """Representation of a Tara binary sensor."""

    entity_description: TaraBinarySensorDescription
    _attr_has_entity_name = False

    def __init__(
        self,
        coordinator: TaraPolarStationCoordinator,
        description: TaraBinarySensorDescription,
        entry_id: str,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_name = f"Tara {description.key.replace('_', ' ').title()}"
        self._attr_unique_id = f"{entry_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            name=NAME,
            manufacturer="Tara Ocean Foundation",
            model="Polar Station",
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def is_on(self) -> bool | None:
        """Return whether entity is on."""
        if not self.coordinator.data:
            return None
        return self.entity_description.value_fn(self.coordinator.data)
