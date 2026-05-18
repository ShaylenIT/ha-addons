"""HA Retention Manager - integration package (skeleton).

This file contains minimal setup entrypoints used by Home Assistant to
discover the integration. The full implementation will live across
`sensor.py`, `services.py`, and other helper modules.
"""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_ALLOWED_DIRECTORIES, CONF_POLLING_MINUTES, DOMAIN, PLATFORMS
from .coordinator import RetentionManagerCoordinator


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the integration from YAML configuration (not used).

    This integration primarily uses config entries; YAML setup is a
    no-op placeholder for now.
    """
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up the integration from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    config = entry.options if hasattr(entry, "options") else {}
    allowed = config.get(CONF_ALLOWED_DIRECTORIES, entry.data.get(CONF_ALLOWED_DIRECTORIES, []))
    polling_interval = config.get(CONF_POLLING_MINUTES, entry.data.get(CONF_POLLING_MINUTES, 30))

    coordinator = RetentionManagerCoordinator(hass, entry, allowed, polling_interval)
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN]["allowed_directories"] = allowed
    hass.data[DOMAIN]["coordinator"] = coordinator
    hass.data[DOMAIN]["last_action"] = {
        "timestamp": None,
        "files_processed": 0,
        "last_run_type": None,
        "dirs_removed": 0,
        "errors": [],
    }

    from . import services

    hass.services.async_register("file_manager", "purge", services.async_handle_purge)
    hass.services.async_register("file_manager", "refresh_stats", services.async_handle_refresh)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry and unregister services."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    try:
        hass.services.async_remove("file_manager", "purge")
        hass.services.async_remove("file_manager", "refresh_stats")
    except Exception:
        pass

    hass.data[DOMAIN].pop("coordinator", None)
    hass.data[DOMAIN].pop("allowed_directories", None)
    hass.data[DOMAIN].pop("last_action", None)

    return unload_ok
