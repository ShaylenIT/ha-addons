# File Purge Manager — Data Model

This document defines the primary entities and JSON-like schemas used by the File Purge Manager integration.

## AllowedDirectory (configuration)
- path: string (absolute)
- label: string? (optional human-friendly name)
- enabled: bool
- id: string (stable identifier)

Example:
```
{
  "id": "media_snapshots",
  "path": "/media/snapshots",
  "label": "Camera snapshots",
  "enabled": true
}
```

## DirectoryMonitorSensor (runtime entity)
- entity_id: string (e.g. `sensor.media_snapshots_stats`)
- path: string
- state: int (total bytes)
- attributes:
  - file_count: int
  - oldest_file_timestamp: ISO-8601 string | null
  - path: string
  - last_scanned: ISO-8601 string

## LastActionTracker (runtime entity)
- entity_id: `sensor.file_manager_last_action`
- state: ISO-8601 timestamp
- attributes:
  - files_processed: int
  - last_run_type: enum {"Dry","Live"}
  - dirs_removed: int
  - errors: list[string]

## PurgeRequest (service input)
- path: string (must match an AllowedDirectory)
- filename_filter: string (glob)
- age_days: int (optional)
- dry_run: bool (default: true)
- recursive: bool (default: false)
- remove_empty_dirs: bool (default: false)

Validation rules:
- `path` is required and must be in allowed directories.
- `age_days` must be >= 0 if provided.

## PurgeResult (service response)
- requested_path: string
- matched_files: list[{path: string, size_bytes: int, mtime: ISO-8601}]
- deleted_files: list[{path: string, size_bytes: int}]  # empty if dry_run
- removed_dirs: list[string]
- errors: list[{path: string, error: string}]
- summary: {matched: int, deleted: int, dirs_removed: int}

## RefreshRequest (service input)
- path: string? (optional; omit to refresh all allowed directories)

Behavioral notes
- Path validation occurs against both the integration `AllowedDirectory` list and HA's global `allowlist_external_dirs`.
- Directory removal uses bottom-up traversal; entries in `removed_dirs` should be returned in removal order.
- All timestamps use ISO-8601 (UTC) strings.

*** End of data model
