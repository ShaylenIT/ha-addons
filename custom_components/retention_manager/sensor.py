"""Sensor platform for Retention Manager."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import RetentionManagerCoordinator


def _sanitize_entity_name(path: str) -> str:
    name = path.strip("/\\").replace("/", "_").replace("\\", "_")
    return name if name else "root"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: RetentionManagerCoordinator = hass.data[DOMAIN]["coordinator"]
    entities: list[CoordinatorEntity] = []

    for path in coordinator.allowed_directories:
        entities.append(DirectoryStatsSensor(coordinator, path))

    async_add_entities(entities, True)


class DirectoryStatsSensor(CoordinatorEntity):
    """Sensor representing directory statistics."""

    def __init__(self, coordinator: RetentionManagerCoordinator, path: str) -> None:
        super().__init__(coordinator)
        self._path = path
        self._attr_name = f"{_sanitize_entity_name(path)} stats"
        self._attr_unique_id = f"retention_manager_{_sanitize_entity_name(path)}"

    @property
    def name(self) -> str:
        return self._attr_name

    @property
    def unique_id(self) -> str:
        return self._attr_unique_id

    @property
    def state(self) -> int | None:
        data = self.coordinator.data
        if data is None or self._path not in data:
            return None
        return data[self._path].total_bytes

    @property
    def extra_state_attributes(self) -> dict[str, str | int | None]:
        data = self.coordinator.data
        if data is None or self._path not in data:
            return {}

        stats = data[self._path]
        return {
            "file_count": stats.file_count,
            "oldest_file_timestamp": stats.oldest_file_timestamp,
            "path": self._path,
            "last_scanned": stats.last_scanned,
        }
