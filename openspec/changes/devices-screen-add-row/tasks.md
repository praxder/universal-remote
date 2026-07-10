## 1. Banner + list composition (TDD)

- [ ] 1.1 Add `tests/test_tui_devices.py` cases (red): opening Manage Devices with no devices shows exactly one row in `#device-list` and it is the add sentinel (no separator); opening with one or more devices lists the devices first, then a separator, then the add row last
- [ ] 1.2 Replace `Label("Manage Devices", id="devices-title")` with a `Static` rendering the "Devices" ASCII banner (id `devices-title`); add `#devices-title { width: 36; text-align: center; }` to the `CSS` block in `app.py` (green)
- [ ] 1.3 Rewrite `_reload()`: add an `Option(device.name, id=device.id)` per device, then a `Separator()` only when devices exist, then an add `Option("+ add", id="__add__")`; set `highlighted = 0`; remove the `#devices-empty` `Label` from `compose()` and its update in `_reload()` (green)

## 2. Selection behavior (TDD)

- [ ] 2.1 Add `tests/test_tui_devices.py` cases (red): selecting the add row via Enter and via mouse click both push `AddDeviceScreen` (no `existing`); selecting a device row via Enter and via mouse click both push `AddDeviceScreen` with `existing` set to that device
- [ ] 2.2 Add `on_option_list_option_selected`: when `event.option.id == "__add__"` call `action_add()`; otherwise resolve the device by id and push `AddDeviceScreen(existing=device)` (green)
- [ ] 2.3 Add a test confirming `e`/`delete` on the add row are no-ops (the sentinel resolves to no device), and confirm no guard code is needed

## 3. Preflight

- [ ] 3.1 Run the formatter/linter and fix any issues
- [ ] 3.2 Run the full test suite and confirm all tests pass
- [ ] 3.3 Launch the TUI: confirm the "Devices" banner, add-only list on first run, devices + separator + add when devices exist, Enter/click add opens the add flow, and Enter/click on a device opens edit
