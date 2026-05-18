"""Data update coordinator for Retention Manager."""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Dict, List

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed


_LOGGER = logging.getLogger(__name__)


@dataclass
class DirectoryStats:
    total_bytes: int
    file_count: int
    oldest_file_timestamp: str | None
    last_scanned: str


class RetentionManagerCoordinator(DataUpdateCoordinator[Dict[str, DirectoryStats]]):
    """Coordinator that polls configured directories."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        allowed_directories: List[str],
        polling_interval: int,
    ) -> None:
        self.allowed_directories = allowed_directories
        self.entry = entry
        super().__init__(
            hass,
            _LOGGER,
            name="Retention Manager",
            update_interval=timedelta(minutes=polling_interval),
            update_method=self._async_update_data,
        )

    async def _async_update_data(self) -> Dict[str, DirectoryStats]:
        _LOGGER.debug("Coordinator refresh triggered for %s directories", len(self.allowed_directories))
        return await self.hass.async_add_executor_job(self._compute_all_stats)

    def _compute_all_stats(self) -> Dict[str, DirectoryStats]:
        results: Dict[str, DirectoryStats] = {}
        for path in self.allowed_directories:
            _LOGGER.debug("Computing stats for allowed directory: %s", path)
            results[path] = self._compute_path_stats(path)
        _LOGGER.info("Completed coordinator refresh for %d directories", len(results))
        return results

    def _compute_path_stats(self, path: str) -> DirectoryStats:
        total = 0
        count = 0
        oldest = None
        try:
            for dirpath, _, filenames in os.walk(path):
                for filename in filenames:
                    file_path = os.path.join(dirpath, filename)
                    try:
                        st = os.stat(file_path)
                    except FileNotFoundError:
                        continue
                    total += st.st_size
                    count += 1
                    if oldest is None or st.st_mtime < oldest:
                        oldest = st.st_mtime
        except FileNotFoundError as err:
            raise UpdateFailed(f"Directory not found: {path}") from err
        except PermissionError as err:
            _LOGGER.error("Permission denied when scanning %s: %s", path, err)
            raise UpdateFailed(f"Permission denied: {path}") from err

        total_stats = DirectoryStats(
            total_bytes=total,
            file_count=count,
            oldest_file_timestamp=(
                datetime.fromtimestamp(oldest, tz=timezone.utc).isoformat()
                if oldest is not None
                else None
            ),
            last_scanned=datetime.now(timezone.utc).isoformat(),
        )
        _LOGGER.debug("Path %s stats: %s", path, total_stats)
        return total_stats
*** End Patch