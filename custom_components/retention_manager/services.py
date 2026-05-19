"""Service handlers for Retention Manager integration.

Handlers are thin adapters that validate input, run blocking disk
operations in the executor, and update Home Assistant sensors/states.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List

from homeassistant.core import HomeAssistant, ServiceCall

from .const import DOMAIN
from .purge import PurgeRequest, execute_purge

_LOGGER = logging.getLogger(__name__)


def _to_iso(ts: float) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()


async def async_handle_purge(hass: HomeAssistant, call: ServiceCall) -> None:
    data = call.data or {}
    path = data.get("path")
    _LOGGER.debug("Received purge service call with data: %s", data)
    if not path:
        _LOGGER.error("Purge called without path")
        return

    allowed = hass.data.setdefault(DOMAIN, {}).get("allowed_directories", [])
    if path not in allowed:
        _LOGGER.warning("Purge rejected for disallowed path: %s", path)
        rejected_time = _to_iso(time.time())
        hass.states.async_set("sensor.file_manager_last_action", rejected_time, {
            "files_processed": 0,
            "last_run_type": "Rejected",
            "dirs_removed": 0,
            "errors": ["path_not_allowed"],
        })
        return

    request = PurgeRequest(
        path=path,
        filename_filter=data.get("filename_filter", "*"),
        age_days=data.get("age_days"),
        dry_run=data.get("dry_run", True),
        recursive=data.get("recursive", False),
        remove_empty_dirs=data.get("remove_empty_dirs", False),
    )

    result = await hass.async_add_executor_job(execute_purge, request)

    # Update last action sensor
    last_action = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "files_processed": result.summary["matched"],
        "last_run_type": "Dry" if request.dry_run else "Live",
        "dirs_removed": result.summary["dirs_removed"],
        "errors": [e.get("error") for e in result.errors] if result.errors else [],
    }
    hass.data[DOMAIN]["last_action"] = last_action
    hass.states.async_set("sensor.file_manager_last_action", last_action["timestamp"], last_action)

    # Refresh coordinator data to update directory sensors
    coordinator = hass.data[DOMAIN].get("coordinator")
    if coordinator is not None:
        await coordinator.async_request_refresh()

    _LOGGER.info(
        "Purge completed for %s: matched=%s deleted=%s removed_dirs=%s errors=%s",
        path,
        result.summary["matched"],
        result.summary["deleted"],
        result.summary["dirs_removed"],
        result.errors,
    )


async def async_handle_refresh(hass: HomeAssistant, call: ServiceCall) -> None:
    data = call.data or {}
    path = data.get("path")

    allowed = hass.data.setdefault(DOMAIN, {}).get("allowed_directories", [])
    if path and path not in allowed:
        _LOGGER.warning("Refresh rejected for disallowed path: %s", path)
        return

    _LOGGER.debug("Received refresh service call for path=%s", path)
    coordinator = hass.data[DOMAIN].get("coordinator")
    if coordinator is None:
        _LOGGER.error("No coordinator available for refresh")
        return

    if path:
        stats = await hass.async_add_executor_job(coordinator._compute_path_stats, path)
        current_data = dict(coordinator.data or {})
        current_data[path] = stats
        coordinator.async_set_updated_data(current_data)
        _LOGGER.info("Path-scoped refresh completed for %s", path)
    else:
        await coordinator.async_request_refresh()
        _LOGGER.info("Full refresh completed for all allowed directories")

