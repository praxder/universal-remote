## 1. Store-level conflict detection

- [x] 1.1 In `tests/test_device_crud.py`, add failing tests for `DeviceStore.find_conflict`: duplicate name (case-insensitive, whitespace-trimmed) returns the name message, duplicate IP returns the IP message, unique name+IP returns `None`, name collision reported when both collide, and `exclude_id` skips the matching device.
- [x] 1.2 Add `find_conflict(name, ip, exclude_id=None) -> str | None` to `DeviceStore` in `src/universal_remote/devices/store.py` per the design (name checked before IP; `casefold()`+`strip()` for name, exact trimmed for IP).
- [x] 1.3 Run the store tests until green.

## 2. Guard the save flow with an inline error

- [x] 2.1 In `tests/test_tui_devices.py`, add failing tests: adding a device with a duplicate name shows the `#error` label and leaves the store unchanged/screen still open; adding a duplicate IP does the same; a unique add still saves and pops; editing a device unchanged still saves (self excluded); editing onto another device's name is blocked with the error shown.
- [x] 2.2 Add `yield Label("", id="error")` between `#ip` and `#save` in `AddDeviceScreen.compose`.
- [x] 2.3 In `AddDeviceScreen._save`, call `store.find_conflict(name, ip, exclude_id=self._existing.id if self._existing else None)`; on a message, set the `#error` label and `return` without saving; on `None`, clear the label, add/update, and pop as today.
- [x] 2.4 Run the TUI tests until green.

## 3. Preflight

- [x] 3.1 Format and lint the changed files.
- [x] 3.2 Run the full test suite and confirm it passes.
