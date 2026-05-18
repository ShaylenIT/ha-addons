import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from custom_components.retention_manager.coordinator import RetentionManagerCoordinator, DirectoryStats


class DummyHass:
    def async_add_executor_job(self, job, *args):
        return job(*args)


def test_compute_path_stats_returns_directory_metrics(tmp_path: Path) -> None:
    content = "hello"
    file_a = tmp_path / "a.txt"
    file_b = tmp_path / "b.log"
    file_a.write_text(content)
    file_b.write_text(content)

    coordinator = RetentionManagerCoordinator(DummyHass(), None, [str(tmp_path)], 1)
    stats = coordinator._compute_path_stats(str(tmp_path))

    assert isinstance(stats, DirectoryStats)
    assert stats.file_count == 2
    assert stats.total_bytes == len(content) * 2
    assert stats.oldest_file_timestamp is not None
    assert stats.last_scanned is not None


def test_compute_all_stats_aggregates_all_allowed_directories(tmp_path: Path) -> None:
    path1 = tmp_path / "dir1"
    path2 = tmp_path / "dir2"
    path1.mkdir()
    path2.mkdir()
    (path1 / "one.txt").write_text("1")
    (path2 / "two.txt").write_text("22")

    coordinator = RetentionManagerCoordinator(DummyHass(), None, [str(path1), str(path2)], 1)
    all_stats = coordinator._compute_all_stats()

    assert str(path1) in all_stats
    assert str(path2) in all_stats
    assert all_stats[str(path1)].file_count == 1
    assert all_stats[str(path2)].total_bytes == 2
