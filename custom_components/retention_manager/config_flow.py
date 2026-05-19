import logging
import voluptuous as vol
from homeassistant import config_entries
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Retention Manager."""

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="Retention Manager", data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({}),
        )
