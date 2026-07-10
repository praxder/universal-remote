## 1. Tests (red)

- [x] 1.1 Update the two-device delete test in `tests/test_tui_devices.py` to press `backspace` (not `delete`), then confirm the prompt, and assert only the targeted device is removed
- [x] 1.2 Add a test: highlight a device, press `backspace`, cancel the prompt, assert the device is still in the store
- [x] 1.3 Update the add-row no-op test to press `backspace` and assert no prompt appears and the store stays empty
- [x] 1.4 Run the suite and confirm the new/updated tests fail for the expected reasons

## 2. Implementation (green)

- [x] 2.1 Add a `ConfirmDeleteScreen(ModalScreen[bool])` in `devices_screen.py` showing the device name with Confirm/Cancel buttons; Escape and Cancel dismiss `False`, Confirm dismisses `True`
- [x] 2.2 Change the `DeviceListScreen` binding from `("delete", "delete", "Delete")` to `("backspace", "delete", "Delete")`
- [x] 2.3 Rewrite `action_delete` to resolve the selected device, return early if none, then push `ConfirmDeleteScreen` with a callback that calls `store.delete(id)` + `_reload()` only when the result is `True`
- [x] 2.4 Run the suite and confirm all tests pass

## 3. Preflight

- [x] 3.1 Format and lint the changed files
- [x] 3.2 Run the full test suite green
- [x] 3.3 Validate the change: `openspec validate confirm-device-delete`

## 4. Refine confirmation UX

- [x] 4.1 Add a test: open the prompt, assert focus starts on cancel, press an arrow key, assert focus moves between the confirm and cancel buttons (run red)
- [x] 4.2 Add arrow-key bindings (up/left → focus previous, down/right → focus next) and focus the cancel button on mount
- [x] 4.3 Add app-level CSS so the modal renders as a translucent centered pop-up over the device list with a bordered dialog box
- [x] 4.4 Run the suite green, format + lint
- [x] 4.5 Render the open prompt to a screenshot and confirm the device list shows through behind the dialog (visual check for the pop-up)
- [x] 4.6 Re-validate the change
