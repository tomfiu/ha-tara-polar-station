"""Entity creation tests for Tara platforms."""

from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from typing import Any

import pytest

pytest.importorskip("homeassistant")

from custom_components.tara_polar_station.binary_sensor import (
    BINARY_SENSOR_TYPES,
    TaraBinarySensorEntity,
)
from custom_components.tara_polar_station.sensor import SENSOR_TYPES, TaraSensorEntity


def _coordinator_with_data() -> Any:
    return SimpleNamespace(
        data={
            "latitude": 79.332,
            "longitude": -23.992,
            "speed": 0.3,
            "course": 40.0,
            "last_report": datetime(2026, 3, 8, 12, 30, tzinfo=timezone.utc),
            "distance_from_home": 100.0,
            "distance_to_north_pole": 1200.0,
            "bearing_from_home": "N",
            "days_since_departure": 10,
            "solar_elevation": -8.0,
            "mission_phase": "drift",
            "in_arctic_circle": True,
            "in_polar_day": False,
            "in_polar_night": True,
            "stationary": True,
            "is_stale": False,
            "raw_telemetry": {"source": "mock"},
            "local_sunrise": None,
            "local_sunset": None,
        }
    )


def test_sensor_entities_expose_values() -> None:
    """Each sensor description should produce an entity value."""
    coordinator = _coordinator_with_data()
    for description in SENSOR_TYPES:
        entity = TaraSensorEntity(coordinator, description, "entry")  # type: ignore[arg-type]
        assert entity.native_value is not None


def test_binary_sensor_entities_expose_boolean_state() -> None:
    """Each binary sensor description should produce boolean state."""
    coordinator = _coordinator_with_data()
    for description in BINARY_SENSOR_TYPES:
        entity = TaraBinarySensorEntity(coordinator, description, "entry")  # type: ignore[arg-type]
        assert entity.is_on is not None
