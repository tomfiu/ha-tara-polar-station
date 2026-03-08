"""Sensor entities for Tara Polar Station."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfAngle, UnitOfLength, UnitOfSpeed
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, NAME
from .coordinator import TaraPolarStationCoordinator

ValueFn = Callable[[dict[str, Any]], Any]


@dataclass(frozen=True, kw_only=True)
class TaraSensorEntityDescription(SensorEntityDescription):
    """Sensor description with data extraction callback."""

    value_fn: ValueFn


SENSOR_TYPES: tuple[TaraSensorEntityDescription, ...] = (
    TaraSensorEntityDescription(
        key="latitude",
        translation_key="latitude",
        value_fn=lambda data: data.get("latitude"),
        icon="mdi:latitude",
    ),
    TaraSensorEntityDescription(
        key="longitude",
        translation_key="longitude",
        value_fn=lambda data: data.get("longitude"),
        icon="mdi:longitude",
    ),
    TaraSensorEntityDescription(
        key="speed",
        translation_key="speed",
        value_fn=lambda data: data.get("speed"),
        native_unit_of_measurement=UnitOfSpeed.KILOMETERS_PER_HOUR,
        icon="mdi:speedometer",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    TaraSensorEntityDescription(
        key="course",
        translation_key="course",
        value_fn=lambda data: data.get("course"),
        native_unit_of_measurement=UnitOfAngle.DEGREES,
        icon="mdi:compass-rose",
    ),
    TaraSensorEntityDescription(
        key="last_report",
        translation_key="last_report",
        value_fn=lambda data: data.get("last_report"),
        device_class=SensorDeviceClass.TIMESTAMP,
        icon="mdi:clock-outline",
    ),
    TaraSensorEntityDescription(
        key="distance_from_home",
        translation_key="distance_from_home",
        value_fn=lambda data: data.get("distance_from_home"),
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        icon="mdi:home-map-marker",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    TaraSensorEntityDescription(
        key="distance_to_north_pole",
        translation_key="distance_to_north_pole",
        value_fn=lambda data: data.get("distance_to_north_pole"),
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        icon="mdi:snowflake",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    TaraSensorEntityDescription(
        key="bearing_from_home",
        translation_key="bearing_from_home",
        value_fn=lambda data: data.get("bearing_from_home"),
        icon="mdi:compass",
    ),
    TaraSensorEntityDescription(
        key="days_since_departure",
        translation_key="days_since_departure",
        value_fn=lambda data: data.get("days_since_departure"),
        icon="mdi:calendar-clock",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    TaraSensorEntityDescription(
        key="solar_elevation",
        translation_key="solar_elevation",
        value_fn=lambda data: data.get("solar_elevation"),
        native_unit_of_measurement=UnitOfAngle.DEGREES,
        icon="mdi:weather-sunny",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    TaraSensorEntityDescription(
        key="local_sunrise",
        translation_key="local_sunrise",
        value_fn=lambda data: data.get("local_sunrise"),
        device_class=SensorDeviceClass.TIMESTAMP,
        icon="mdi:weather-sunset-up",
    ),
    TaraSensorEntityDescription(
        key="local_sunset",
        translation_key="local_sunset",
        value_fn=lambda data: data.get("local_sunset"),
        device_class=SensorDeviceClass.TIMESTAMP,
        icon="mdi:weather-sunset-down",
    ),
    TaraSensorEntityDescription(
        key="mission_phase",
        translation_key="mission_phase",
        value_fn=lambda data: data.get("mission_phase"),
        icon="mdi:ship-wheel",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Tara sensor entities from a config entry."""
    coordinator: TaraPolarStationCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        TaraSensorEntity(coordinator, description, entry.entry_id)
        for description in SENSOR_TYPES
    )


class TaraSensorEntity(CoordinatorEntity[TaraPolarStationCoordinator], SensorEntity):
    """Representation of a Tara Polar Station sensor."""

    entity_description: TaraSensorEntityDescription
    _attr_has_entity_name = False

    def __init__(
        self,
        coordinator: TaraPolarStationCoordinator,
        description: TaraSensorEntityDescription,
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
    def native_value(self) -> Any:
        """Return sensor value."""
        data = self.coordinator.data or {}
        value = self.entity_description.value_fn(data)
        if isinstance(value, datetime):
            return value
        return value

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return extra attributes."""
        if not self.coordinator.data:
            return None
        if self.entity_description.key != "last_report":
            return None
        return {
            "local_sunrise": self.coordinator.data.get("local_sunrise"),
            "local_sunset": self.coordinator.data.get("local_sunset"),
            "is_stale": self.coordinator.data.get("is_stale"),
            "source": self.coordinator.data.get("raw_telemetry", {}).get("source"),
        }
