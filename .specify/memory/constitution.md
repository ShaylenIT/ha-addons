<!--
Sync Impact Report:
- Updated project constitution from template to concrete governance for HA Retention Manager.
- Defined safety, test-first, integration, observability, and security principles.
- No downstream artifacts were automatically updated because only the constitution file changed.
-->

# HA Retention Manager Constitution

## Core Principles

### I. Safe File Operations
All integration behavior must be explicit, permissioned, and non-destructive by default.
- Direct file deletion only occurs when an explicit `dry_run: false` purge is requested.
- The integration must reject requests for any path not listed in `allowed_directories`.
- Service calls, path validation, and sensor refresh behavior must be auditable through logs and entity state.

### II. Test-First Development
Every feature and regression fix must be accompanied by automated tests before being declared complete.
- Unit tests for core logic and file system behavior are mandatory.
- Integration-style tests for HA service handlers and coordinator refresh logic are required.
- New behavior must include failing tests before implementation and passing tests after.

### III. Integration and Observability
Home Assistant custom integrations must behave like first-class HA components.
- Use `DataUpdateCoordinator` for polling and sensor refresh semantics.
- Keep I/O off the event loop using `async_add_executor_job`.
- Provide clear logging for service calls, refresh operations, file deletion, and errors.

### IV. Minimal Dependency and Compatibility
Dependencies should be limited to what is necessary for Home Assistant integration and maintain compatibility with HA-supported Python versions.
- Prefer standard library operations for file scanning and deletion.
- Keep the integration compatible with Home Assistant 2024.x and Python 3.11+.

### V. Documentation and Developer Experience
Documentation must clearly explain installation, configuration, and testing.
- README and quickstart content must align with the implemented integration functionality.
- Testing commands should be included for local validation.
- Security notes and service usage examples must be present.

## Security and Safety Requirements
- The integration is explicitly allowlisted: only configured directories may be scanned or purged.
- Service inputs are validated; disallowed operations are logged and rejected without side effects.
- `dry_run` is the safe default for purge operations to avoid unintended deletion.

## Development Workflow
- Use the repository root as the reference path for tests and imports.
- Maintain clear task tracking in `tasks.md` or the todo list when `tasks.md` is absent.
- Apply implementation changes incrementally, with each task validated by tests or documentation updates.

## Governance
This constitution is the authoritative guide for feature design and implementation in this repository.
- Any deviation from these principles requires explicit documentation and approval from the repository owner.
- Code changes should reference constitution principles when making safety, testing, or security trade-offs.

**Version**: 1.0.0 | **Ratified**: 2026-05-18 | **Last Amended**: 2026-05-18
