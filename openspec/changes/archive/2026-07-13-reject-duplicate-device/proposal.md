## Why

The Add/Edit Device screen saves any device the user enters, so nothing stops two saved devices from sharing the same name or IP address. Duplicate names make the device list ambiguous, and two entries pointing at the same IP are almost always a mistake. The user should be told before the save happens.

## What Changes

- Before saving a device (both Add and Edit), reject the save when its name (case-insensitive, trimmed) or IP (trimmed) matches another already-saved device.
- Show an inline error on the Add/Edit screen naming which field collided (e.g. "A device named 'Living Room' already exists." or "A device with IP 10.0.0.5 already exists."); the user stays on the screen to fix it.
- On Edit, the device being edited is excluded from the comparison (by `id`) so re-saving a device with its own unchanged name/IP still succeeds.
- Add a `DeviceStore.find_conflict(name, ip, exclude_id=None)` method that returns a message string for the first collision or `None` when the values are unique.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `device-management`: adds a requirement that duplicate name or IP is rejected on save, and constrains the existing Add/Edit behavior to enforce it.

## Impact

- `src/universal_remote/devices/store.py`: new `find_conflict` method.
- `src/universal_remote/tui/devices_screen.py`: `AddDeviceScreen` gains an inline error `Label` and a guard in `_save`.
- Tests: `tests/test_device_crud.py` (store-level conflict detection), `tests/test_tui_devices.py` (blocked save + error shown, self-exclusion on edit).
- No data migration; no change to the persisted file format.
