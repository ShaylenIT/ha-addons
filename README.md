# Quickstart — HA Retention Manager

This quickstart guide walks through installation, configuration, and testing for the custom Home Assistant integration.

## 1. Install the integration

### HACS (recommended)

1. Open **HACS** → **Integrations** → ⋮ menu → **Custom repositories**
2. Add this repository URL and select category **Integration**
3. Install **HA Retention Manager**
4. Restart Home Assistant

### Manual install

1. Copy `custom_components/retention_manager/` to `config/custom_components/`
2. Restart Home Assistant

## 2. Add the integration

1. Go to **Settings → Devices & Services → Add Integration**
2. Search for **File Purge Manager**
3. Configure:
   - **Allowed Directories**: absolute directories the integration may scan or purge
   - **Polling Interval**: interval in minutes for sensor refresh
   - **Enable Manual Service**: whether `file_manager.refresh_stats` is available

## 3. Verify entities

After setup, the integration creates:

- `sensor.<directory_name>_stats`
- `sensor.file_manager_last_action`

These entities update after each scheduled poll and immediately after service calls.

## 4. Use services

### Purge files

```yaml
service: file_manager.purge
data:
  path: "/media/snapshots"
  filename_filter: "*.jpg"
  age_days: 30
  dry_run: true
  recursive: true
  remove_empty_dirs: true
```

### Refresh stats

```yaml
service: file_manager.refresh_stats
# Optional path field:
# data:
#   path: "/backup"
```

## 5. Example automation

```yaml
alias: "Nightly Snapshot Cleanup"
trigger:
  - platform: time
    at: "02:00:00"
action:
  - service: file_manager.purge
    data:
      path: "/media/snapshots"
      filename_filter: "*.jpg"
      age_days: 14
      dry_run: false
      recursive: true
      remove_empty_dirs: true
```

## 6. Notes

- The integration only operates on directories explicitly listed in `Allowed Directories`.
- `file_manager.purge` performs a full sensor refresh after completing a purge.
- `file_manager.refresh_stats` supports path-scoped refresh and full refresh of all allowed directories.
