"""Config flow for Parcels App integration."""

from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN, CONF_API_KEY, CONF_DESTINATION_COUNTRY


class ParcelsAppConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Parcels App."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, str] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(
                step_id="user",
                data_schema=vol.Schema(
                    {
                        vol.Required(CONF_API_KEY): str,
                        vol.Required(CONF_DESTINATION_COUNTRY): str,
                    }
                ),
            )

        errors = {}

        try:
            # Validate the API key here if possible
            # For now, we'll just accept any input
            return self.async_create_entry(title="Parcels App", data=user_input)
        except Exception:  # pylint: disable=broad-except
            errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_API_KEY): str,
                    vol.Required(CONF_DESTINATION_COUNTRY): str,
                }
            ),
            errors=errors,
        )
