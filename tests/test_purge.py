import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from custom_components.retention_manager.purge import (
    PurgeRequest,
    delete_files,
    execute_purge,
    find_matched_files,
    remove_empty_dirs_bottom_up,
)


def write_file(path: Path, content: str = "data") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def test_find_matched_files_filters_by_glob(tmp_path: Path) -> None:
    write_file(tmp_path / "keep.txt")
    write_file(tmp_path / "skip.log")

    matched = find_matched_files(str(tmp_path), "*.txt")

    assert len(matched) == 1
    assert matched[0]["path"].endswith("keep.txt")


def test_find_matched_files_recursive(tmp_path: Path) -> None:
    nested = tmp_path / "subdir" / "old.txt"
    write_file(nested)

    matched = find_matched_files(str(tmp_path), "*.txt", recursive=True)

    assert len(matched) == 1
    assert nested.samefile(matched[0]["path"])


def test_find_matched_files_age_filters_by_mtime(tmp_path: Path) -> None:
    old_file = tmp_path / "old.txt"
    new_file = tmp_path / "new.txt"
    write_file(old_file)
    write_file(new_file)

    old_time = time.time() - 3 * 86400
    os.utime(old_file, (old_time, old_time))

    matched = find_matched_files(str(tmp_path), "*.txt", age_days=2)

    assert len(matched) == 1
    assert matched[0]["path"].endswith("old.txt")


def test_delete_files_respects_dry_run(tmp_path: Path) -> None:
    target = tmp_path / "delete_me.txt"
    write_file(target)
    files = [{"path": str(target), "size_bytes": target.stat().st_size}]

    deleted, errors = delete_files(files, dry_run=True)

    assert deleted == []
    assert errors == []
    assert target.exists()


def test_delete_files_removes_file(tmp_path: Path) -> None:
    target = tmp_path / "delete_me.txt"
    write_file(target)
    files = [{"path": str(target), "size_bytes": target.stat().st_size}]

    deleted, errors = delete_files(files, dry_run=False)

    assert len(deleted) == 1
    assert deleted[0]["path"] == str(target)
    assert errors == []
    assert not target.exists()


def test_execute_purge_dry_run_returns_matches(tmp_path: Path) -> None:
    target = tmp_path / "old.txt"
    write_file(target)
    old_time = time.time() - 3 * 86400
    os.utime(target, (old_time, old_time))

    request = PurgeRequest(
        path=str(tmp_path),
        filename_filter="*.txt",
        age_days=2,
        dry_run=True,
        recursive=False,
        remove_empty_dirs=True,
    )
    result = execute_purge(request)

    assert result.requested_path == str(tmp_path)
    assert result.summary["matched"] == 1
    assert result.summary["deleted"] == 0
    assert result.deleted_files == []
    assert result.errors == []


def test_execute_purge_live_deletes_file_and_removes_empty_dirs(tmp_path: Path) -> None:
    target_dir = tmp_path / "a"
    target_dir.mkdir()
    target = target_dir / "old.txt"
    write_file(target)
    old_time = time.time() - 3 * 86400
    os.utime(target, (old_time, old_time))

    request = PurgeRequest(
        path=str(tmp_path),
        filename_filter="*.txt",
        age_days=2,
        dry_run=False,
        recursive=True,
        remove_empty_dirs=True,
    )
    result = execute_purge(request)

    assert result.summary["matched"] == 1
    assert result.summary["deleted"] == 1
    assert result.deleted_files[0]["path"] == str(target)
    assert str(target_dir) in result.removed_dirs
    assert not target.exists()


def test_remove_empty_dirs_bottom_up(tmp_path: Path) -> None:
    deep_dir = tmp_path / "a" / "b"
    deep_dir.mkdir(parents=True)

    removed = remove_empty_dirs_bottom_up(str(tmp_path))

    assert str(deep_dir) in removed
    # because root becomes empty after removing nested dirs, it may also be removed
    assert any(part.endswith("a") for part in removed) or any(part == str(tmp_path) for part in removed)
