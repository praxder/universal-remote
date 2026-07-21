## 1. Tests (red)

- [ ] 1.1 In `tests/test_tui_devices.py`, add a test: opening the edit flow (`AddDeviceScreen(existing=device)`) shows a Delete button below Save.
- [ ] 1.2 Add a test: the add flow (`AddDeviceScreen()`) shows no Delete button.
- [ ] 1.3 Add a test: activating the Delete button pushes `ConfirmDeleteScreen` and the device is still in the store while the prompt is open.
- [ ] 1.4 Add a test: confirming the edit-screen delete removes the device from the store and pops back to the device list.
- [ ] 1.5 Add a test: cancelling the edit-screen delete leaves the store unchanged and stays on the edit screen.
- [ ] 1.6 Add a test: the Delete button is reachable via Down-arrow focus movement from Save on the edit screen.

## 2. Implementation (green)

- [ ] 2.1 In `AddDeviceScreen.compose`, yield a `Button("Delete", id="delete", variant="error")` after Save, only when `self._existing is not None`.
- [ ] 2.2 In `on_button_pressed`, handle `id == "delete"`: push `ConfirmDeleteScreen(self._existing.name)` with a callback that, on confirm, calls `self.app.store.delete(self._existing.id)` then `self.app.pop_screen()`.
- [ ] 2.3 Add CSS in `src/universal_remote/tui/app.py` for `#add-device #delete` matching Save's left alignment and top margin.

## 3. Preflight

- [ ] 3.1 Run the formatter and linter; fix any issues.
- [ ] 3.2 Run the full test suite; confirm all tests pass.
- [ ] 3.3 Verify the edit screen visually (screenshot) shows the Delete button aligned below Save; confirm Add screen has none.
- [ ] 3.4 Run `openspec validate add-edit-device-delete-button --strict` and resolve any errors.
