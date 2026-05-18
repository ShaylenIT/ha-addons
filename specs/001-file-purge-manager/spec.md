# Feature Specification: File Purge Manager (Integration)

**Feature Branch**: `[001-file-purge-manager]`

**Created**: 2026-05-18

**Status**: Draft

**Input**: User description: "Create specs per feature"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Configure file purge integration (Priority: P1)

A Home Assistant administrator configures the File Purge Manager integration to monitor approved local directories, set the polling interval, and enable or disable the manual refresh service.

**Why this priority**: Configuration is the entry point for the feature and prevents unwanted file operations outside approved paths.

**Independent Test**: Configure the integration with one allowed directory, a 30-minute polling interval, and manual refresh enabled. Validate that settings are accepted and saved.

**Acceptance Scenarios**:

1. **Given** the integration is not configured, **When** the user enters allowed directories, polling interval, and toggles manual refresh, **Then** the integration stores those values and begins monitoring the approved directories.
2. **Given** the integration is configured, **When** the user opens the integration settings, **Then** they see the current allowed directories, polling interval, and manual refresh enabled state.

---

### User Story 2 - Purge old files safely (Priority: P2)

A user runs the `file_manager.purge` service to delete files from an approved directory by filename pattern or age, and views updated directory statistics immediately after the purge.

**Why this priority**: File cleanup is the core value of the feature and must work reliably with immediate feedback.

**Independent Test**: Call the purge service with a valid allowed path, filename filter, and age threshold; verify the service identifies the correct files, deletes them when `dry_run` is false, and refreshes sensor values.

**Acceptance Scenarios**:

1. **Given** a configured allowed directory containing old files, **When** the user calls `file_manager.purge` with `age_days` and `filename_filter`, **Then** files matching the criteria are deleted and sensors refresh immediately.
2. **Given** `dry_run` is true, **When** the purge service runs, **Then** no files are deleted and the response reports the files that would have been processed.
3. **Given** `remove_empty_dirs` is true, **When** the purge completes, **Then** any directories left empty under the target path are removed without failing if new files appear concurrently.

---

### User Story 3 - Refresh directory stats on demand (Priority: P3)

A user triggers `file_manager.refresh_stats` after a high-volume event so the directory-monitoring sensors reflect current disk usage immediately.

**Why this priority**: Manual refresh supports automation scenarios and lets users get up-to-date information without waiting for the next polling interval.

**Independent Test**: Call `file_manager.refresh_stats` with and without `path`; verify sensors refresh for the requested directory or for all approved directories.

**Acceptance Scenarios**:

1. **Given** the integration is configured, **When** the user calls `file_manager.refresh_stats` with no path, **Then** all allowed directories refresh their sensors immediately.
2. **Given** the integration is configured, **When** the user calls `file_manager.refresh_stats` with a specific allowed path, **Then** only that directory refreshes.
3. **Given** the path is not in the allowed directories list, **When** refresh_stats is called, **Then** the call is rejected and logged.

---

### Edge Cases

- What happens when the user provides a path that is not in the allowed directory list? The system must reject the request and retain current monitoring state.
- How does the integration behave if a directory becomes unavailable between poll cycles? The system must surface a sensor error state or log the failure without crashing.
- How does the purge service behave if a file is deleted by another process during the operation? The service must handle file-not-found gracefully and continue processing remaining files.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The integration MUST allow users to configure a list of allowed absolute directories where purge and refresh operations may operate.
- **FR-002**: The integration MUST allow users to set a polling interval in minutes with a valid range of 1 to 1440.
- **FR-003**: The integration MUST allow users to enable or disable the `file_manager.refresh_stats` service separately from the purge functionality.
- **FR-004**: The integration MUST expose a directory monitor sensor for each allowed directory with state representing total directory size and attributes for file count, oldest file timestamp, and path.
- **FR-005**: The integration MUST expose a `sensor.file_manager_last_action` sensor with state as the timestamp of the most recent file manager activity and attributes for files processed, run type, and directories removed.
- **FR-006**: The integration MUST provide the `file_manager.purge` service with fields: `path`, `filename_filter`, `age_days`, `dry_run`, `recursive`, and `remove_empty_dirs`.
- **FR-007**: The integration MUST provide the `file_manager.refresh_stats` service with an optional `path` field that refreshes either a specific allowed directory or all allowed directories when omitted.
- **FR-008**: The integration MUST enforce path validation so purge and refresh operations are rejected when the requested path is not listed in allowed directories.
- **FR-009**: The integration MUST maintain a dual security model by validating paths against both the integration's allowed directories list and Home Assistant's global allowlist.
- **FR-010**: The integration MUST remove empty directories after a successful purge when `remove_empty_dirs` is true, using a safe bottom-up traversal.
- **FR-011**: The integration MUST refresh directory sensors immediately after any purge operation or manual refresh service call.

### Key Entities *(include if feature involves data)*

- **Allowed Directory Configuration**: Represents each user-defined absolute directory path permitted for monitoring and file operations.
- **Directory Monitor Sensor**: Represents runtime state for an allowed directory including total size, file count, oldest file timestamp, and path.
- **Last Action Tracker Sensor**: Represents the timestamp and metadata for the most recent purge or refresh operation.
- **Purge Request**: Represents the fields submitted to the `file_manager.purge` service.
- **Refresh Request**: Represents the optional path submitted to `file_manager.refresh_stats`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can complete integration setup with allowed directories, polling interval, and manual refresh toggle in a single configuration flow.
- **SC-002**: Sensors for allowed directories refresh at the configured polling interval and also refresh immediately after purge or manual refresh requests.
- **SC-003**: The `file_manager.purge` service identifies files matching the provided filter and age criteria and deletes them when `dry_run` is false.
- **SC-004**: The `file_manager.purge` service reports no deletions when `dry_run` is true and still returns the files that would have been processed.
- **SC-005**: The `file_manager.refresh_stats` service refreshes current metrics for a specific allowed directory when a path is supplied and for all allowed directories when no path is supplied.
- **SC-006**: Any request for a path outside the configured allowed directories is rejected, logged, and does not alter sensor state.
- **SC-007**: When `remove_empty_dirs` is enabled, empty directories are removed after purge without failing if new files appear concurrently.

## Assumptions

- Users are operating Home Assistant on a system with locally mounted directories and have appropriate file access permissions for the configured paths.
- Path matching for `filename_filter` will use glob-style patterns and will be applied only within the requested allowed directory.
- The integration will rely on Home Assistant's existing global file allowlist for additional security checks.
- Directory monitoring sensors are refreshed by a shared coordinator so multiple allowed directories do not trigger duplicate scans.
- Mobile or remote UI-specific workflows are out of scope for this feature; the focus is on the Home Assistant integration and service behavior.
