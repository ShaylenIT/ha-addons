# API Contracts — File Purge Manager

This document specifies the public service contracts and sensor attributes.

## Services

### `file_manager.purge`

Request (YAML/JSON):
- `path` (string) REQUIRED — absolute path; must be in AllowedDirectories
- `filename_filter` (string) OPTIONAL — glob pattern; default `*`
- `age_days` (int) OPTIONAL — delete files older than this many days
- `dry_run` (bool) OPTIONAL — default `true`; if `true`, no files are removed
- `recursive` (bool) OPTIONAL — default `false`
- `remove_empty_dirs` (bool) OPTIONAL — default `false`

Validation:
- `path` must match an AllowedDirectory and HA's global `allowlist_external_dirs`.
- `age_days` must be >= 0 if present.

Response (JSON):
- `requested_path`: string
- `matched_files`: list of {`path`, `size_bytes`, `mtime`}
- `deleted_files`: list of {`path`, `size_bytes`} (empty if `dry_run`)
- `removed_dirs`: list[string]
- `errors`: list of {`path`, `error`}
- `summary`: {`matched`, `deleted`, `dirs_removed`}

Errors:
- 400: Invalid input (missing `path` or invalid types)
- 403: Path not allowed (not in AllowedDirectories or global allowlist)
- 500: Internal failure (partial successes reported in `errors`)

Side effects:
- Directory sensors for affected paths are refreshed synchronously after purge completion.
- `sensor.file_manager_last_action` updated with run metadata.

### `file_manager.refresh_stats`

Request:
- `path` (string) OPTIONAL — when omitted, refresh all AllowedDirectories

Response:
- `refreshed_paths`: list[string]
- `errors`: list[{`path`, `error`}]

Errors:
- 403: Path not allowed
- 500: Internal failure (partial successes reported)

Side effects:
- Sensors refreshed for requested directories.

## Sensors

### `sensor.<dir_name>_stats`
- State: total bytes (int)
- Attributes:
  - `file_count` (int)
  - `oldest_file_timestamp` (ISO-8601 | null)
  - `path` (string)
  - `last_scanned` (ISO-8601)

### `sensor.file_manager_last_action`
- State: ISO-8601 timestamp
- Attributes:
  - `files_processed` (int)
  - `last_run_type` ("Dry" | "Live")
  - `dirs_removed` (int)
  - `errors` (list[string])

## Notes
- All timestamps are ISO-8601 UTC.
- Deletion operations are performed via executor jobs to avoid blocking the event loop.
- Implementations must prefer non-blocking patterns and return informative partial results on failure.

