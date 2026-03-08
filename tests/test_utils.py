"""Unit tests for Tara utility functions."""

from __future__ import annotations

from datetime import datetime, timezone

from custom_components.tara_polar_station.utils import (
    bearing_to_compass,
    calculate_polar_context,
    haversine_distance_km,
    initial_bearing_degrees,
    parse_coordinates,
)


def test_haversine_distance_km() -> None:
    """Distance between Prague and Berlin should be roughly 280 km."""
    distance = haversine_distance_km(50.0755, 14.4378, 52.52, 13.405)
    assert 275 <= distance <= 285


def test_initial_bearing_degrees() -> None:
    """Bearing from Prague to Berlin should be NW-ish."""
    bearing = initial_bearing_degrees(50.0755, 14.4378, 52.52, 13.405)
    assert 330 <= bearing <= 350
    assert bearing_to_compass(bearing) in {"NNW", "NW"}


def test_parse_coordinates() -> None:
    """Coordinates parser validates ranges and format."""
    assert parse_coordinates("79.332,-23.992") == (79.332, -23.992)
    assert parse_coordinates("") is None


def test_parse_coordinates_invalid() -> None:
    """Invalid coordinates should fail."""
    try:
        parse_coordinates("hello")
    except ValueError:
        pass
    else:  # pragma: no cover - explicit failure path
        raise AssertionError("Expected ValueError")


def test_calculate_polar_context_returns_solar_elevation() -> None:
    """Solar context should always provide a numeric solar elevation."""
    context = calculate_polar_context(
        latitude=79.332,
        longitude=-23.992,
        moment=datetime(2026, 3, 8, 12, tzinfo=timezone.utc),
    )
    assert isinstance(context.solar_elevation, float)
