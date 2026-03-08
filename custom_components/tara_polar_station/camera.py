"""Optional webcam camera for Tara Polar Station."""

from __future__ import annotations

import logging
from typing import Any

from aiohttp import ClientError

from homeassistant.components.camera import Camera
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CAMERA_SCAN_INTERVAL,
    DOMAIN,
    WEB_CAM_DEFAULT_STILL_IMAGE_URL,
    WEB_CAM_NAME,
)

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = CAMERA_SCAN_INTERVAL


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Tara camera entity."""
    async_add_entities([TaraPolarStationCamera(hass, entry)])


class TaraPolarStationCamera(Camera):
    """Camera entity for Tara Polar Station public webcam."""

    _attr_has_entity_name = False
    _attr_name = WEB_CAM_NAME

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize camera entity."""
        super().__init__()
        self.hass = hass
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_camera"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Tara Polar Station Tracker",
            manufacturer="Tara Ocean Foundation",
            model="Polar Station",
            entry_type=DeviceEntryType.SERVICE,
        )
        self._still_image_url = WEB_CAM_DEFAULT_STILL_IMAGE_URL
        self._content_type = "image/jpeg"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return camera metadata."""
        return {"still_image_url": self._still_image_url}

    async def async_camera_image(
        self, width: int | None = None, height: int | None = None
    ) -> bytes | None:
        """Return a still image from the public webcam."""
        del width, height
        session = async_get_clientsession(self.hass)
        try:
            async with session.get(self._still_image_url, timeout=20) as response:
                if response.status != 200:
                    _LOGGER.debug(
                        "Webcam image request failed with status %s", response.status
                    )
                    return None
                return await response.read()
        except (TimeoutError, ClientError) as err:
            _LOGGER.debug("Webcam image request failed: %s", err)
            return None
