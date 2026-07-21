## Why

The remote screen's top status bar shows only `Remote — <device name>`, so a user driving one of several similar devices cannot confirm at a glance which device they are actually controlling. Showing the name, type, and IP address makes the active target unambiguous.

## What Changes

- Replace the remote screen's status-bar text with `Name: <name> • Type: <type> • IP: <ip>`, dropping the `Remote —` prefix entirely.
- `<type>` uses the platform's existing human-readable label (the same label the device-type picker shows), not the raw platform identifier.

## Capabilities

### New Capabilities
<!-- none -->

### Modified Capabilities
- `tui-remote`: add a requirement fixing the content of the remote screen's status bar to the device's name, human-readable type, and IP address.

## Impact

- `src/universal_remote/tui/remote_screen.py` — the title assignment on mount (currently `f"Remote — {self._device.name}"`).
- New test coverage for the status-bar text (none exists today).
- No API, dependency, or store changes.
