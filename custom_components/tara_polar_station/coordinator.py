"""Coordinator for Tara Polar Station data."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timedelta, timezone
import logging
from typing import Any

from aiohttp import ClientError, ClientSession

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import (
    API_ENDPOINTS,
    API_TIMEOUT_SECONDS,
    ARCTIC_CIRCLE_LATITUDE,
    ATTR_IS_STALE,
    ATTR_RAW_TELEMETRY,
    CONF_HOME_COORDINATES_OVERRIDE,
    CONF_POLL_INTERVAL,
    DEFAULT_POLL_INTERVAL_MINUTES,
    DEFAULT_STATIONARY_SPEED_KMH,
    EVENT_ENTERED_ARCTIC_CIRCLE,
    EVENT_ENTERED_POLAR_NIGHT,
    EVENT_POSITION_UPDATED,
    EVENT_RESUMED_TRANSIT,
    EVENT_STATIONARY,
    EXPEDITION_DEPARTURE_DATE,
    NORTH_POLE_LATITUDE,
    NORTH_POLE_LONGITUDE,
)
from .utils import (
    bearing_to_compass,
    calculate_polar_context,
    haversine_distance_km,
    initial_bearing_degrees,
    parse_coordinates,
)

_LOGGER = logging.getLogger(__name__)


class TaraApiError(Exception):
    """Base API exception for Tara telemetry retrieval."""


class TaraMalformedDataError(TaraApiError):
    """Raised when telemetry response cannot be parsed."""


class TaraTelemetryApiClient:
    """HTTP client for Tara Polar Station telemetry."""

    def __init__(self, session: ClientSession) -> None:
        self._session = session

    async def async_fetch_telemetry(self) -> dict[str, Any]:
        """Fetch and normalize telemetry from available API endpoints."""
        last_error: Exception | None = None
        for endpoint in API_ENDPOINTS:
            try:
                telemetry = await self._async_fetch_from_endpoint(endpoint)
                telemetry["source"] = endpoint
                return telemetry
            except TaraApiError as err:
                _LOGGER.debug("Telemetry endpoint failed %s: %s", endpoint, err)
                last_error = err
            except Exception as err:  # pragma: no cover - defensive guard
                _LOGGER.debug("Unexpected telemetry endpoint failure %s: %s", endpoint, err)
                last_error = TaraApiError(str(err))

        raise TaraApiError(
            f"Unable to retrieve Tara telemetry from all endpoints: {last_error}"
        )

    async def _async_fetch_from_endpoint(self, endpoint: str) -> dict[str, Any]:
        """Fetch telemetry payload from one endpoint."""
        try:
            async with self._session.get(endpoint, timeout=API_TIMEOUT_SECONDS) as response:
                if response.status != 200:
                    raise TaraApiError(f"Endpoint returned status {response.status}")
                payload = await response.json(content_type=None)
        except (TimeoutError, ClientError) as err:
            raise TaraApiError(f"Request failed: {err}") from err

        return self._parse_payload(payload)

    def _parse_payload(self, payload: Any) -> dict[str, Any]:
        """Extract telemetry from various API payload formats."""
        candidates = _extract_candidates(payload)
        for candidate in candidates:
            parsed = _parse_telemetry_candidate(candidate)
            if parsed is not None:
                return parsed
        raise TaraMalformedDataError("No telemetry object with usable coordinates found")


class TaraPolarStationCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """DataUpdateCoordinator for Tara Polar Station telemetry and analytics."""

    config_entry: ConfigEntry

    def __init__(
        self, hass: HomeAssistant, config_entry: ConfigEntry, session: ClientSession
    ) -> None:
        self.config_entry = config_entry
        self._client = TaraTelemetryApiClient(session)
        self._home_coordinates_override = parse_coordinates(
            config_entry.options.get(CONF_HOME_COORDINATES_OVERRIDE)
        )
        interval_minutes = int(
            config_entry.options.get(CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL_MINUTES)
        )
        super().__init__(
            hass,
            _LOGGER,
            name="Tara Polar Station Coordinator",
            update_interval=timedelta(minutes=interval_minutes),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch and enrich telemetry."""
        raw = await self._client.async_fetch_telemetry()
        _LOGGER.debug("Received telemetry: %s", raw)

        try:
            state = self._build_state(raw)
        except TaraMalformedDataError as err:
            _LOGGER.warning("Malformed telemetry payload: %s", err)
            if self.data:
                stale = {**self.data, ATTR_IS_STALE: True}
                return stale
            raise UpdateFailed(str(err)) from err
        except Exception as err:
            raise UpdateFailed(f"Unexpected telemetry processing error: {err}") from err

        self._fire_events(state)
        return state

    def _build_state(self, raw: Mapping[str, Any]) -> dict[str, Any]:
        """Build derived integration state from normalized telemetry."""
        latitude = float(raw["latitude"])
        longitude = float(raw["longitude"])
        speed = float(raw.get("speed", 0.0))
        course = float(raw.get("course", 0.0))
        reported_at = _ensure_utc_datetime(raw["timestamp"])

        home_latitude, home_longitude = self._home_coordinates_override or (
            self.hass.config.latitude,
            self.hass.config.longitude,
        )

        distance_from_home = haversine_distance_km(
            home_latitude, home_longitude, latitude, longitude
        )
        distance_to_north_pole = haversine_distance_km(
            latitude, longitude, NORTH_POLE_LATITUDE, NORTH_POLE_LONGITUDE
        )
        bearing_degrees = initial_bearing_degrees(
            home_latitude, home_longitude, latitude, longitude
        )

        polar_context = calculate_polar_context(latitude, longitude, reported_at)
        days_since_departure = max(
            0, (reported_at.date() - EXPEDITION_DEPARTURE_DATE).days
        )
        stationary = speed <= DEFAULT_STATIONARY_SPEED_KMH

        return {
            "latitude": round(latitude, 6),
            "longitude": round(longitude, 6),
            "speed": round(speed, 2),
            "course": round(course, 1),
            "last_report": reported_at,
            "distance_from_home": round(distance_from_home, 1),
            "distance_to_north_pole": round(distance_to_north_pole, 1),
            "bearing_from_home": bearing_to_compass(bearing_degrees),
            "days_since_departure": days_since_departure,
            "mission_phase": "drift" if stationary else "transit",
            "in_arctic_circle": latitude >= ARCTIC_CIRCLE_LATITUDE,
            "in_polar_day": polar_context.in_polar_day,
            "in_polar_night": polar_context.in_polar_night,
            "stationary": stationary,
            "solar_elevation": round(polar_context.solar_elevation, 2),
            "local_sunrise": polar_context.sunrise,
            "local_sunset": polar_context.sunset,
            ATTR_IS_STALE: False,
            ATTR_RAW_TELEMETRY: dict(raw),
        }

    def _fire_events(self, state: Mapping[str, Any]) -> None:
        """Publish telemetry and milestone events on HA event bus."""
        payload = {
            "latitude": state["latitude"],
            "longitude": state["longitude"],
            "speed": state["speed"],
            "distance_to_pole": state["distance_to_north_pole"],
            "timestamp": state["last_report"].isoformat(),
        }
        self.hass.bus.async_fire(EVENT_POSITION_UPDATED, payload)

        previous = self.data or {}
        if previous:
            if not previous.get("in_arctic_circle") and state["in_arctic_circle"]:
                self.hass.bus.async_fire(EVENT_ENTERED_ARCTIC_CIRCLE, payload)

            if not previous.get("in_polar_night") and state["in_polar_night"]:
                self.hass.bus.async_fire(EVENT_ENTERED_POLAR_NIGHT, payload)

            if not previous.get("stationary") and state["stationary"]:
                self.hass.bus.async_fire(EVENT_STATIONARY, payload)

            if previous.get("stationary") and not state["stationary"]:
                self.hass.bus.async_fire(EVENT_RESUMED_TRANSIT, payload)


def _extract_candidates(payload: Any) -> list[Mapping[str, Any]]:
    """Collect possible telemetry dictionaries from nested payloads."""
    candidates: list[Mapping[str, Any]] = []

    def _maybe_append(item: Any) -> None:
        if isinstance(item, Mapping):
            candidates.append(item)

    if isinstance(payload, Mapping):
        _maybe_append(payload)
        for key in ("data", "result", "position", "telemetry", "features"):
            value = payload.get(key)
            if isinstance(value, list):
                for item in value:
                    _maybe_append(item)
                    if isinstance(item, Mapping):
                        _maybe_append(item.get("properties"))
            else:
                _maybe_append(value)
                if isinstance(value, Mapping):
                    _maybe_append(value.get("properties"))
    elif isinstance(payload, list):
        for item in payload:
            _maybe_append(item)

    return candidates


def _parse_telemetry_candidate(candidate: Mapping[str, Any]) -> dict[str, Any] | None:
    """Parse one telemetry candidate object."""
    latitude = _pick_first(candidate, ("latitude", "lat", "y"))
    longitude = _pick_first(candidate, ("longitude", "lon", "lng", "x"))
    if latitude is None or longitude is None:
        geometry = candidate.get("geometry")
        if isinstance(geometry, Mapping):
            coords = geometry.get("coordinates")
            if isinstance(coords, list) and len(coords) >= 2:
                longitude = longitude or coords[0]
                latitude = latitude or coords[1]

    if latitude is None or longitude is None:
        return None

    speed = _pick_first(candidate, ("speed", "sog", "speed_over_ground", "velocity"))
    course = _pick_first(candidate, ("course", "cog", "heading"))
    timestamp_raw = _pick_first(
        candidate,
        ("timestamp", "time", "last_update", "reported_at", "datetime", "date"),
    )

    timestamp = _parse_timestamp(timestamp_raw)
    if timestamp is None:
        timestamp = dt_util.utcnow()

    try:
        return {
            "latitude": float(latitude),
            "longitude": float(longitude),
            "speed": float(speed) if speed is not None else 0.0,
            "course": float(course) if course is not None else 0.0,
            "timestamp": timestamp,
        }
    except (TypeError, ValueError):
        return None


def _pick_first(source: Mapping[str, Any], keys: tuple[str, ...]) -> Any:
    """Return first non-null value from a set of candidate keys."""
    for key in keys:
        value = source.get(key)
        if value is not None:
            return value
    return None


def _parse_timestamp(value: Any) -> datetime | None:
    """Parse timestamp from common formats."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return _ensure_utc_datetime(value)
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, tz=timezone.utc)
    if isinstance(value, str):
        parsed = dt_util.parse_datetime(value)
        if parsed is not None:
            return _ensure_utc_datetime(parsed)
    return None


def _ensure_utc_datetime(value: datetime) -> datetime:
    """Ensure datetime is timezone-aware UTC."""
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)
