"""Constants for the Tara Polar Station integration."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Final

from homeassistant.const import Platform

DOMAIN: Final = "tara_polar_station"
NAME: Final = "Tara Polar Station Tracker"
VERSION: Final = "0.1.0"

PLATFORMS: Final[list[Platform]] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.CAMERA,
]
BASE_PLATFORMS: Final[list[Platform]] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
]

CONF_POLL_INTERVAL: Final = "poll_interval"
CONF_HOME_COORDINATES_OVERRIDE: Final = "home_coordinates_override"
CONF_ENABLE_WEBCAM: Final = "enable_webcam"

DEFAULT_POLL_INTERVAL_MINUTES: Final = 15
DEFAULT_ENABLE_WEBCAM: Final = False
DEFAULT_STATIONARY_SPEED_KMH: Final = 1.0
CAMERA_SCAN_INTERVAL: Final = timedelta(minutes=5)

NORTH_POLE_LATITUDE: Final = 90.0
NORTH_POLE_LONGITUDE: Final = 0.0
ARCTIC_CIRCLE_LATITUDE: Final = 66.5
EXPEDITION_DEPARTURE_DATE: Final = date(2026, 1, 1)

ATTR_RAW_TELEMETRY: Final = "raw_telemetry"
ATTR_IS_STALE: Final = "is_stale"

EVENT_POSITION_UPDATED: Final = "tara_position_updated"
EVENT_ENTERED_ARCTIC_CIRCLE: Final = "tara_entered_arctic_circle"
EVENT_ENTERED_POLAR_NIGHT: Final = "tara_entered_polar_night"
EVENT_STATIONARY: Final = "tara_stationary"
EVENT_RESUMED_TRANSIT: Final = "tara_resumed_transit"

WEB_CAM_NAME: Final = "Tara Polar Station"
WEB_CAM_DEFAULT_STILL_IMAGE_URL: Final = (
    "https://tara-polar-station.panomax.com/cams/1/latest.jpg"
)

API_TIMEOUT_SECONDS: Final = 20
API_ENDPOINTS: Final[tuple[str, ...]] = (
    "https://api.taraocean.org/polar-station/telemetry",
    "https://taraocean.org/wp-json/tara/v1/polar-station",
    "https://www.taraocean.org/wp-json/tara/v1/polar-station",
)

STORAGE_VERSION: Final = 1
STORAGE_KEY: Final = f"{DOMAIN}_last_state"
