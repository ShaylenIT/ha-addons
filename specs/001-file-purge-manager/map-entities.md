# Entity to User Story Mapping

This document maps the primary data entities to the user stories defined in `spec.md`.

- AllowedDirectory (config)
  - User Story 1: Configure file purge integration
  - Why: Defines the set of absolute paths the integration can operate on; core to configuration flow and security.

- DirectoryMonitorSensor (runtime entity)
  - User Story 1: visible in integration settings
  - User Story 3: Refresh directory stats on demand
  - Why: Provides immediate and periodic metrics for each allowed directory.

- LastActionTracker (runtime entity)
  - User Story 2: Purge old files safely
  - Why: Shows the last purge/refresh action and metadata like files processed and run type.

- PurgeRequest (service input)
  - User Story 2: Purge old files safely
  - Why: Captures filters, age thresholds, and flags required to perform safe purge operations.

- PurgeResult (service response)
  - User Story 2: Purge old files safely
  - Why: Returns matched and deleted files, errors, and summary for immediate feedback.

- RefreshRequest (service input)
  - User Story 3: Refresh directory stats on demand
  - Why: Lets a user request immediate sensor refresh for specific or all allowed directories.

Behavioral mappings
- Path validation (FR-008/FR-009) maps to User Story 1 and is enforced by services used in Story 2/3.
- `remove_empty_dirs` behavior (FR-010) maps to PurgeResult removed_dirs and to sensors updated in Story 2.

