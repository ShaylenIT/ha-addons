import logging
import voluptuous as vol
from homeassistant import config_entries
from .const import DOMAIN, CONF_ALLOWED_DIRECTORIES, CONF_POLLING_MINUTES, CONF_MANUAL_REFRESH

_LOGGER = logging.getLogger(__name__)

DEFAULT_POLLING_MINUTES = 30

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Retention Manager."""

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            # Validate allowed directories: must be non-empty, absolute paths
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
