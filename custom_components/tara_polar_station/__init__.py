"""Tara Polar Station integration bootstrap."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

    from .coordinator import TaraPolarStationCoordinator

    TaraPolarStationConfigEntry = ConfigEntry[TaraPolarStationCoordinator]
else:
    TaraPolarStationConfigEntry = Any

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: dict[str, Any]) -> bool:
    """Set up integration from YAML (not used)."""
    del hass, config
    return True


async def async_setup_entry(
    hass: HomeAssistant, entry: TaraPolarStationConfigEntry
) -> bool:
    """Set up Tara Polar Station from a config entry."""
    from homeassistant.const import Platform
    from homeassistant.helpers.aiohttp_client import async_get_clientsession

    from .const import BASE_PLATFORMS, CONF_ENABLE_WEBCAM, DOMAIN
    from .coordinator import TaraPolarStationCoordinator

    session = async_get_clientsession(hass)
    coordinator = TaraPolarStationCoordinator(hass, entry, session)

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    entry.async_on_unload(entry.add_update_listener(_async_reload_entry))

    platforms: list[Platform] = list(BASE_PLATFORMS)
    if entry.options.get(CONF_ENABLE_WEBCAM, False):
        platforms.append(Platform.CAMERA)

    await hass.config_entries.async_forward_entry_setups(entry, platforms)
    hass.async_create_task(coordinator.async_refresh())
    _LOGGER.debug("Scheduled initial Tara telemetry refresh in background")
    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: TaraPolarStationConfigEntry
) -> bool:
    """Unload Tara Polar Station config entry."""
    from homeassistant.const import Platform

    from .const import BASE_PLATFORMS, CONF_ENABLE_WEBCAM, DOMAIN

    platforms: list[Platform] = list(BASE_PLATFORMS)
    if entry.options.get(CONF_ENABLE_WEBCAM, False):
        platforms.append(Platform.CAMERA)

    unload_ok = await hass.config_entries.async_unload_platforms(entry, platforms)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


async def _async_reload_entry(
    hass: HomeAssistant, entry: TaraPolarStationConfigEntry
) -> None:
    """Reload on options change."""
    await hass.config_entries.async_reload(entry.entry_id)
