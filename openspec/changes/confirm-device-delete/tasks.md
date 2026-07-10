## 1. Tests (red)

- [ ] 1.1 Update the two-device delete test in `tests/test_tui_devices.py` to press `backspace` (not `delete`), then confirm the prompt, and assert only the targeted device is removed
- [ ] 1.2 Add a test: highlight a device, press `backspace`, cancel the prompt, assert the device is still in the store
- [ ] 1.3 Update the add-row no-op test to press `backspace` and assert no prompt appears and the store stays empty
- [ ] 1.4 Run the suite and confirm the new/updated tests fail for the expected reasons

## 2. Implementation (green)

- [ ] 2.1 Add a `ConfirmDeleteScreen(ModalScreen[bool])` in `devices_screen.py` showing the device name with Confirm/Cancel buttons; Escape and Cancel dismiss `False`, Confirm dismisses `True`
- [ ] 2.2 Change the `DeviceListScreen` binding from `("delete", "delete", "Delete")` to `("backspace", "delete", "Delete")`
- [ ] 2.3 Rewrite `action_delete` to resolve the selected device, return early if none, then push `ConfirmDeleteScreen` with a callback that calls `store.delete(id)` + `_reload()` only when the result is `True`
- [ ] 2.4 Run the suite and confirm all tests pass

## 3. Preflight

- [ ] 3.1 Format and lint the changed files
- [ ] 3.2 Run the full test suite green
- [ ] 3.3 Validate the change: `openspec validate confirm-device-delete`
