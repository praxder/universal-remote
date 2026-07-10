## 1. Remote-control core

- [x] 1.1 Remove `POWER` from the `Key` enum in `keys.py`
- [x] 1.2 Remove the `power_on` flag from `Capabilities` in `capabilities.py`
- [x] 1.3 Update `test_keys.py` so the expected key set no longer includes power
- [x] 1.4 Update `test_capabilities.py` to drop the `power_on` assertions

## 2. Device model and store

- [x] 2.1 Remove the `mac` and `model` fields from `Device` in `devices/models.py`
- [x] 2.2 Make `Device.from_dict` filter incoming data to the dataclass's known field names so legacy `mac`/`model` keys are ignored
- [x] 2.3 Update `test_device_crud.py` to remove mac/model usage
- [x] 2.4 Add/adjust `test_store.py`: legacy entry with `mac`/`model` loads cleanly and those keys are absent on re-save

## 3. Adapters

- [x] 3.1 Samsung (`adapters/samsung.py`): remove `Key.POWER: "KEY_POWER"` from `SAMSUNG_KEYS`, drop `power_on=True` from `_CAPABILITIES`, and delete `power_on()`, `PowerOnResult`, the `wol`/`send_magic_packet` import and constructor param
- [x] 3.2 LG (`adapters/lg.py`): remove `Key.POWER` from `_SUPPORTED_KEYS`, remove the `if key is Key.POWER: power_off()` branch in `_dispatch_key`, drop `power_on=True` from `_CAPABILITIES`, and delete `power_on()`, `PowerOnResult`, the `wol`/`send_magic_packet` import and constructor param
- [x] 3.3 Update `test_samsung_adapter.py`: remove power_on tests and the power key from capability/mapping assertions
- [x] 3.4 Update `test_lg_adapter.py`: remove power_on tests, the power-off mapping test, and the power key from capability assertions
- [x] 3.5 Update `tests/fakes.py` if it declares power support or a WoL hook

## 4. Remove probe

- [x] 4.1 Delete `src/universal_remote/devices/probe.py`
- [x] 4.2 Remove the `probe`/`ProbeResult`/`probe_device` import, constructor param, and `self.probe` attribute from `tui/app.py`
- [x] 4.3 Delete `tests/test_probe.py`
- [x] 4.4 Remove probe references from `test_cli_integration.py` and any other test that injects a probe

## 5. Add/Edit Device screen

- [x] 5.1 In `tui/devices_screen.py`, remove the Model and MAC `Input`s, the Probe `Button`, the `_probe()` method, and the probe branch in `on_button_pressed`
- [x] 5.2 Remove model/mac prefill in `on_mount` and model/mac read/assignment in `_save` (both add and edit paths); update the class docstring
- [x] 5.3 Add `ADD_TITLE_ART` and `EDIT_TITLE_ART` ASCII banners (same figlet style as `TITLE_ART`) and render the correct one in a `Static` based on `self._existing`, replacing the `Label` title
- [x] 5.4 Update `test_tui_devices.py`: drop probe/model/mac coverage; assert manual IP + Name save and the ASCII banner for both add and edit

## 6. Remote surface

- [x] 6.1 In `tui/remote_screen.py`, remove the Power `_key_button` from `row-top`
- [x] 6.2 Update `test_tui_remote_surface.py` (and `test_tui_capabilities.py` if it references power) to drop the power button

## 7. Styling

- [x] 7.1 In `app.py` CSS, add a rule for the add/edit title `Static` with `width` wide enough for the banner and `margin: 1 0 2 0` (matching `#devices-title`)
- [x] 7.2 In `app.py` CSS, give the Save button left padding matching the input fields' left edge and top margin/padding to separate it from the inputs

## 8. Dependency

- [x] 8.1 Remove `wakeonlan` from `pyproject.toml` dependencies and re-sync the environment

## 9. Preflight

- [x] 9.1 Grep the tree for lingering `power`, `probe`, `wakeonlan`, `.mac`, `.model`, `PowerOnResult` references and clean up any stragglers
- [x] 9.2 Format, lint, and run the full test suite; fix failures
- [x] 9.3 Launch the TUI and verify: Add/Edit screen shows the ASCII banner with correct spacing and only IP + Name; Save is aligned and separated; the remote surface has no Power button
