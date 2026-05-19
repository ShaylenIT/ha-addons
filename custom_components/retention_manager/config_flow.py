import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from .const import DOMAIN, CONF_ALLOWED_DIRECTORIES, CONF_POLLING_MINUTES, CONF_MANUAL_REFRESH, DEFAULT_POLLING_MINUTES

_LOGGER = logging.getLogger(__name__)

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Retention Manager."""

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            dirs = [d.strip() for d in user_input[CONF_ALLOWED_DIRECTORIES].split(',') if d.strip()]
            if not dirs or not all(d.startswith('/') or d[1:3] == ':\\' for d in dirs):
                errors[CONF_ALLOWED_DIRECTORIES] = "invalid_directories"
            elif not (1 <= user_input[CONF_POLLING_MINUTES] <= 1440):
                errors[CONF_POLLING_MINUTES] = "invalid_polling"
            else:
                return self.async_create_entry(
                    title="Retention Manager",
                    data={
                        CONF_ALLOWED_DIRECTORIES: dirs,
                        CONF_POLLING_MINUTES: user_input[CONF_POLLING_MINUTES],
                        CONF_MANUAL_REFRESH: user_input[CONF_MANUAL_REFRESH],
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_ALLOWED_DIRECTORIES, default="/config"): str,
                vol.Required(CONF_POLLING_MINUTES, default=DEFAULT_POLLING_MINUTES): vol.All(int, vol.Range(min=1, max=1440)),
                vol.Required(CONF_MANUAL_REFRESH, default=True): bool,
            }),
            errors=errors,
        )

@callback
def async_get_options_flow(config_entry):
    return OptionsFlow(config_entry)

class OptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        errors = {}
        data = self.config_entry.options or self.config_entry.data
        if user_input is not None:
            dirs = [d.strip() for d in user_input[CONF_ALLOWED_DIRECTORIES].split(',') if d.strip()]
            if not dirs or not all(d.startswith('/') or d[1:3] == ':\\' for d in dirs):
                errors[CONF_ALLOWED_DIRECTORIES] = "invalid_directories"
            elif not (1 <= user_input[CONF_POLLING_MINUTES] <= 1440):
                errors[CONF_POLLING_MINUTES] = "invalid_polling"
            else:
                return self.async_create_entry(
                    title="",
                    data={
                        CONF_ALLOWED_DIRECTORIES: dirs,
                        CONF_POLLING_MINUTES: user_input[CONF_POLLING_MINUTES],
                        CONF_MANUAL_REFRESH: user_input[CONF_MANUAL_REFRESH],
                    },
                )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Required(CONF_ALLOWED_DIRECTORIES, default=','.join(data.get(CONF_ALLOWED_DIRECTORIES, ['/config']))): str,
                vol.Required(CONF_POLLING_MINUTES, default=data.get(CONF_POLLING_MINUTES, DEFAULT_POLLING_MINUTES)): vol.All(int, vol.Range(min=1, max=1440)),
                vol.Required(CONF_MANUAL_REFRESH, default=data.get(CONF_MANUAL_REFRESH, True)): bool,
            }),
            errors=errors,
        )
