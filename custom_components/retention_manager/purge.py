"""Prototype purge algorithm utilities.

This module provides a small, testable prototype of the file selection
and deletion logic described in the spec. It is intentionally
standalone and uses only the Python standard library so it can be
iterated independently of Home Assistant integration code.
"""
from __future__ import annotations

import fnmatch
import logging
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

_LOGGER = logging.getLogger(__name__)


@dataclass
class PurgeRequest:
    path: str
    filename_filter: str = "*"
    age_days: Optional[int] = None
    dry_run: bool = True
    recursive: bool = False
    remove_empty_dirs: bool = False


@dataclass
class PurgeResult:
    requested_path: str
    matched_files: List[Dict[str, Any]] = field(default_factory=list)
    deleted_files: List[Dict[str, Any]] = field(default_factory=list)
    removed_dirs: List[str] = field(default_factory=list)
    errors: List[Dict[str, str]] = field(default_factory=list)
    summary: Dict[str, int] = field(default_factory=lambda: {"matched": 0, "deleted": 0, "dirs_removed": 0})


def _to_iso(ts: float) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()


def find_matched_files(
    root_path: str,
    filename_filter: str = "*",
    age_days: Optional[int] = None,
    recursive: bool = False,
) -> List[Dict]:
    """Return list of files matching criteria.

    Each item is a dict: {path, size_bytes, mtime}
    """
    _LOGGER.debug(
        "Finding matched files in %s filter=%s age_days=%s recursive=%s",
        root_path,
        filename_filter,
        age_days,
        recursive,
    )
    results: List[Dict] = []
    if age_days is not None:
        cutoff = time.time() - age_days * 86400
    else:
        cutoff = None

    if recursive:
        for dirpath, _, filenames in os.walk(root_path):
            for name in filenames:
                if not fnmatch.fnmatch(name, filename_filter):
                    continue
                full = os.path.join(dirpath, name)
                try:
                    st = os.stat(full)
                except FileNotFoundError:
                    continue
                if cutoff is not None and st.st_mtime > cutoff:
                    continue
                results.append({"path": full, "size_bytes": st.st_size, "mtime": st.st_mtime})
    else:
        try:
            with os.scandir(root_path) as it:
                for ent in it:
                    if not ent.is_file():
                        continue
                    if not fnmatch.fnmatch(ent.name, filename_filter):
                        continue
                    try:
                        st = ent.stat()
                    except FileNotFoundError:
                        continue
                    if cutoff is not None and st.st_mtime > cutoff:
                        continue
                    results.append({"path": ent.path, "size_bytes": st.st_size, "mtime": st.st_mtime})
        except FileNotFoundError:
            return []

    # Sort by mtime ascending (oldest first)
    results.sort(key=lambda x: x["mtime"])
    _LOGGER.debug("Matched %d files in %s", len(results), root_path)
    return results


def execute_purge(request: PurgeRequest) -> PurgeResult:
    """Execute purge selection and deletion logic for a request."""
    _LOGGER.info(
        "Executing purge request path=%s filter=%s age_days=%s dry_run=%s recursive=%s remove_empty_dirs=%s",
        request.path,
        request.filename_filter,
        request.age_days,
        request.dry_run,
        request.recursive,
        request.remove_empty_dirs,
    )
    matched = find_matched_files(
        request.path,
        request.filename_filter,
        request.age_days,
        request.recursive,
    )

    deleted: List[Dict] = []
    errors: List[Dict] = []
    if not request.dry_run and matched:
        deleted, errors = delete_files(matched, False)

    removed_dirs: List[str] = []
    if request.remove_empty_dirs and not request.dry_run:
        removed_dirs = remove_empty_dirs_bottom_up(request.path)

    result = PurgeResult(
        requested_path=request.path,
        matched_files=matched,
        deleted_files=deleted,
        removed_dirs=removed_dirs,
        errors=errors,
    )
    result.summary = {
        "matched": len(matched),
        "deleted": len(deleted),
        "dirs_removed": len(removed_dirs),
    }
    _LOGGER.info(
        "Purge result for %s: matched=%s deleted=%s removed_dirs=%s errors=%s",
        request.path,
        result.summary["matched"],
        result.summary["deleted"],
        result.summary["dirs_removed"],
        len(result.errors),
    )
    if result.errors:
        _LOGGER.warning("Encountered purge errors for %s: %s", request.path, result.errors)
    return result


def delete_files(files: List[Dict], dry_run: bool = True) -> Tuple[List[Dict], List[Dict]]:
    """Delete files and return (deleted_list, errors).

    `files` expects dicts with `path` and `size_bytes` keys.
    """
    deleted = []
    errors = []
    if dry_run:
        _LOGGER.debug("Dry-run deletion: %d files would be deleted", len(files))
        return [], []

    _LOGGER.info("Deleting %d files", len(files))
    for f in files:
        p = f["path"]
        try:
            os.remove(p)
            deleted.append({"path": p, "size_bytes": f.get("size_bytes", 0)})
        except FileNotFoundError:
            # treat as non-fatal — file was removed concurrently
            _LOGGER.warning("File already missing during delete: %s", p)
            errors.append({"path": p, "error": "not_found"})
        except PermissionError as e:
            _LOGGER.error("Permission denied deleting file %s: %s", p, e)
            errors.append({"path": p, "error": str(e)})
        except OSError as e:
            _LOGGER.error("Failed deleting file %s: %s", p, e)
            errors.append({"path": p, "error": str(e)})

    return deleted, errors


def remove_empty_dirs_bottom_up(root_path: str) -> List[str]:
    """Remove empty directories under `root_path` in bottom-up order.

    Returns a list of removed directory paths.
    """
    removed = []
    for dirpath, dirnames, filenames in os.walk(root_path, topdown=False):
        # If directory contains no files and no subdirectories, it's empty
        try:
            entries = os.listdir(dirpath)
        except FileNotFoundError:
            _LOGGER.debug("Directory disappeared during cleanup: %s", dirpath)
            continue
        except PermissionError:
            _LOGGER.warning("Permission denied while scanning directory for cleanup: %s", dirpath)
            continue
        if not entries:
            try:
                os.rmdir(dirpath)
                removed.append(dirpath)
                _LOGGER.debug("Removed empty directory: %s", dirpath)
            except OSError as e:
                _LOGGER.warning("Failed to remove directory %s during cleanup: %s", dirpath, e)
                continue

    _LOGGER.info("Removed %d empty directories under %s", len(removed), root_path)
    return removed


if __name__ == "__main__":
    # Simple manual run for quick prototyping (dry-run example)
    import argparse

    parser = argparse.ArgumentParser(description="Prototype purge runner")
    parser.add_argument("path")
    parser.add_argument("--filter", default="*")
    parser.add_argument("--age", type=int)
    parser.add_argument("--recursive", action="store_true")
    parser.add_argument("--dry-run", action="store_true", default=True)
    args = parser.parse_args()

    matched = find_matched_files(args.path, args.filter, args.age, args.recursive)
    print(f"Matched {len(matched)} files")
    for m in matched[:20]:
        print(m["path"], m["size_bytes"], _to_iso(m["mtime"]))
