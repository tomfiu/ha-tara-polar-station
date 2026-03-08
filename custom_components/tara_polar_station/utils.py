"""Utility helpers for Tara Polar Station calculations."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from math import asin, atan2, cos, degrees, radians, sin, sqrt

from astral import Observer
from astral.sun import elevation, sun

EARTH_RADIUS_KM = 6371.0


@dataclass(slots=True)
class PolarContext:
    """Calculated polar context for a location and time."""

    solar_elevation: float
    sunrise: datetime | None
    sunset: datetime | None
    in_polar_day: bool
    in_polar_night: bool


def haversine_distance_km(
    latitude_1: float, longitude_1: float, latitude_2: float, longitude_2: float
) -> float:
    """Return distance in kilometers between two WGS84 points."""
    lat1_rad, lon1_rad = radians(latitude_1), radians(longitude_1)
    lat2_rad, lon2_rad = radians(latitude_2), radians(longitude_2)

    delta_lat = lat2_rad - lat1_rad
    delta_lon = lon2_rad - lon1_rad

    h = (
        sin(delta_lat / 2) ** 2
        + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lon / 2) ** 2
    )
    return 2 * EARTH_RADIUS_KM * asin(sqrt(h))


def initial_bearing_degrees(
    latitude_1: float, longitude_1: float, latitude_2: float, longitude_2: float
) -> float:
    """Return initial bearing from point 1 to point 2, normalized to 0-359."""
    lat1_rad, lat2_rad = radians(latitude_1), radians(latitude_2)
    delta_lon = radians(longitude_2 - longitude_1)

    x = sin(delta_lon) * cos(lat2_rad)
    y = cos(lat1_rad) * sin(lat2_rad) - (
        sin(lat1_rad) * cos(lat2_rad) * cos(delta_lon)
    )
    return (degrees(atan2(x, y)) + 360) % 360


def bearing_to_compass(bearing_degrees: float) -> str:
    """Return cardinal/ordinal compass direction for bearing."""
    directions = ("N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE")
    directions += ("S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW")
    index = int((bearing_degrees + 11.25) // 22.5) % 16
    return directions[index]


def parse_coordinates(value: str | None) -> tuple[float, float] | None:
    """Parse '<lat>,<lon>' into a coordinate tuple."""
    if not value:
        return None

    parts = [part.strip() for part in value.split(",", maxsplit=1)]
    if len(parts) != 2:
        raise ValueError("Coordinates must be in format '<lat>,<lon>'")

    latitude = float(parts[0])
    longitude = float(parts[1])
    if not -90 <= latitude <= 90:
        raise ValueError("Latitude must be between -90 and 90")
    if not -180 <= longitude <= 180:
        raise ValueError("Longitude must be between -180 and 180")

    return latitude, longitude


def calculate_polar_context(
    latitude: float, longitude: float, moment: datetime
) -> PolarContext:
    """Calculate solar elevation and detect polar day/polar night."""
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    else:
        moment = moment.astimezone(timezone.utc)

    observer = Observer(latitude=latitude, longitude=longitude)
    solar_altitude = elevation(observer, moment)

    sunrise: datetime | None = None
    sunset: datetime | None = None
    in_polar_day = False
    in_polar_night = False

    try:
        events = sun(observer, date=moment.date(), tzinfo=timezone.utc)
        sunrise = events["sunrise"]
        sunset = events["sunset"]
    except ValueError as err:
        # Astral raises ValueError when the sun is always above/below horizon.
        details = str(err).lower()
        if "always above the horizon" in details:
            in_polar_day = True
        elif "always below the horizon" in details:
            in_polar_night = True
        else:
            raise

    return PolarContext(
        solar_elevation=solar_altitude,
        sunrise=sunrise,
        sunset=sunset,
        in_polar_day=in_polar_day,
        in_polar_night=in_polar_night,
    )
