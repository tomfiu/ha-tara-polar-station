"""Config flow for Tara Polar Station."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONF_ENABLE_WEBCAM,
    CONF_HOME_COORDINATES_OVERRIDE,
    CONF_POLL_INTERVAL,
    DEFAULT_ENABLE_WEBCAM,
    DEFAULT_POLL_INTERVAL_MINUTES,
    DOMAIN,
    NAME,
)
from .utils import parse_coordinates


class TaraPolarStationConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle config flow for Tara Polar Station."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Create entry with no required user input."""
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()
        return self.async_create_entry(title=NAME, data={})

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> "TaraPolarStationOptionsFlow":
        """Get options flow."""
        return TaraPolarStationOptionsFlow(config_entry)


class TaraPolarStationOptionsFlow(config_entries.OptionsFlow):
    """Tara Polar Station options flow."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Manage options."""
        errors: dict[str, str] = {}
        if user_input is not None:
            coordinates_override = user_input[CONF_HOME_COORDINATES_OVERRIDE].strip()
            if coordinates_override:
                try:
                    latitude, longitude = parse_coordinates(coordinates_override)
                except ValueError:
                    errors[CONF_HOME_COORDINATES_OVERRIDE] = "invalid_coordinates"
                else:
                    user_input[CONF_HOME_COORDINATES_OVERRIDE] = f"{latitude},{longitude}"
            else:
                user_input[CONF_HOME_COORDINATES_OVERRIDE] = ""

            if not errors:
                return self.async_create_entry(title="", data=user_input)

        options = self._config_entry.options
        defaults = {
            CONF_POLL_INTERVAL: options.get(
                CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL_MINUTES
            ),
            CONF_HOME_COORDINATES_OVERRIDE: options.get(
                CONF_HOME_COORDINATES_OVERRIDE, ""
            ),
            CONF_ENABLE_WEBCAM: options.get(CONF_ENABLE_WEBCAM, DEFAULT_ENABLE_WEBCAM),
        }

        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_POLL_INTERVAL, default=defaults[CONF_POLL_INTERVAL]
                ): vol.All(vol.Coerce(int), vol.Range(min=5, max=180)),
                vol.Optional(
                    CONF_HOME_COORDINATES_OVERRIDE,
                    default=defaults[CONF_HOME_COORDINATES_OVERRIDE],
                ): str,
                vol.Optional(
                    CONF_ENABLE_WEBCAM, default=defaults[CONF_ENABLE_WEBCAM]
                ): bool,
            }
        )

        return self.async_show_form(step_id="init", data_schema=schema, errors=errors)
