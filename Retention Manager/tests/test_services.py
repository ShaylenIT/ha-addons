import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pytest

from custom_components.retention_manager.const import DOMAIN
from custom_components.retention_manager.coordinator import DirectoryStats
from custom_components.retention_manager.services import async_handle_purge, async_handle_refresh


class DummyStates:
    def __init__(self) -> None:
        self.set_calls = []

    def async_set(self, entity_id: str, state: str, attributes: dict | None = None) -> None:
        self.set_calls.append({"entity_id": entity_id, "state": state, "attributes": attributes or {}})


class DummyHass:
    def __init__(self) -> None:
        self.data: dict[str, object] = {}
        self.states = DummyStates()

    async def async_add_executor_job(self, job, *args):
        return job(*args)


class DummyCall:
    def __init__(self, data: dict) -> None:
        self.data = data


class FakeCoordinator:
    def __init__(self) -> None:
        self.data: dict[str, DirectoryStats] = {}
        self.refreshed = False

    async def async_request_refresh(self) -> None:
        self.refreshed = True

    def async_set_updated_data(self, new_data: dict[str, DirectoryStats]) -> None:
        self.data = new_data

    def _compute_path_stats(self, path: str) -> DirectoryStats:
        return DirectoryStats(
            total_bytes=123,
            file_count=4,
            oldest_file_timestamp=datetime(2020, 1, 1, tzinfo=timezone.utc).isoformat(),
            last_scanned=datetime.now(timezone.utc).isoformat(),
        )


@pytest.mark.asyncio
async def test_async_handle_refresh_path_scoped_updates_coordinator() -> None:
    hass = DummyHass()
    coordinator = FakeCoordinator()
    hass.data[DOMAIN] = {
        "allowed_directories": ["/tmp"],
        "coordinator": coordinator,
    }

    await async_handle_refresh(hass, DummyCall({"path": "/tmp"}))

    assert "/tmp" in coordinator.data
    assert coordinator.data["/tmp"].total_bytes == 123
    assert coordinator.refreshed is False


@pytest.mark.asyncio
async def test_async_handle_refresh_rejected_for_disallowed_path() -> None:
    hass = DummyHass()
    coordinator = FakeCoordinator()
    hass.data[DOMAIN] = {
        "allowed_directories": ["/tmp"],
        "coordinator": coordinator,
    }

    await async_handle_refresh(hass, DummyCall({"path": "/not_allowed"}))

    assert coordinator.data == {}
    assert coordinator.refreshed is False


@pytest.mark.asyncio
async def test_async_handle_purge_rejected_path_sets_last_action() -> None:
    hass = DummyHass()
    hass.data[DOMAIN] = {"allowed_directories": ["/tmp"], "coordinator": FakeCoordinator()}

    await async_handle_purge(hass, DummyCall({"path": "/disallowed"}))

    assert len(hass.states.set_calls) == 1
    last_action = hass.states.set_calls[0]
    assert last_action["entity_id"] == "sensor.file_manager_last_action"
    assert last_action["attributes"]["last_run_type"] == "Rejected"
    assert last_action["attributes"]["errors"] == ["path_not_allowed"]


@pytest.mark.asyncio
async def test_async_handle_refresh_full_refresh_requests_coordinator_refresh() -> None:
    hass = DummyHass()
    coordinator = FakeCoordinator()
    hass.data[DOMAIN] = {
        "allowed_directories": ["/tmp"],
        "coordinator": coordinator,
    }

    await async_handle_refresh(hass, DummyCall({}))

    assert coordinator.refreshed is True


@pytest.mark.asyncio
async def test_async_handle_purge_live_deletes_files_and_refreshes_coordinator(tmp_path: Path) -> None:
    target = tmp_path / "old.txt"
    target.write_text("delete me")
    old_time = time.time() - 3 * 86400
    os.utime(target, (old_time, old_time))

    coordinator = FakeCoordinator()
    hass = DummyHass()
    hass.data[DOMAIN] = {
        "allowed_directories": [str(tmp_path)],
        "coordinator": coordinator,
    }

    await async_handle_purge(
        hass,
        DummyCall(
            {
                "path": str(tmp_path),
                "filename_filter": "*.txt",
                "age_days": 2,
                "dry_run": False,
                "recursive": False,
                "remove_empty_dirs": False,
            }
        ),
    )

    assert not target.exists()
    assert coordinator.refreshed is True
    assert hass.data[DOMAIN]["last_action"]["last_run_type"] == "Live"
    assert hass.data[DOMAIN]["last_action"]["files_processed"] == 1
