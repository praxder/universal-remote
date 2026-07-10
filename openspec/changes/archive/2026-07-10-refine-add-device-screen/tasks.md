## 1. Adapter display name

- [x] 1.1 Add `display_name: str` to the `Adapter` protocol in `adapter.py`
- [x] 1.2 Declare `display_name = "Samsung Tizen"` on `SamsungTizenAdapter`
- [x] 1.3 Declare `display_name = "LG WebOS"` on `LgWebOsAdapter`
- [x] 1.4 Give `FakeAdapter` (`tests/fakes.py`) a `display_name`, defaulting to its platform id when not supplied
- [x] 1.5 Add assertions to `test_samsung_adapter.py` and `test_lg_adapter.py` that each adapter exposes its display name and keeps its platform id

## 2. Registry exposure

- [x] 2.1 Add `AdapterRegistry.adapters() -> list[Adapter]` returning registered adapters in registration order (keep `platforms()`)
- [x] 2.2 Add `test_registry.py` coverage for `adapters()`

## 3. Field order, friendly labels, read-only edit type

- [x] 3.1 Reorder `AddDeviceScreen.compose` cells to device type, then Name, then IP address
- [x] 3.2 Build the add-mode platform `Select` options from `registry.adapters()` as `(display_name, platform)` tuples, defaulting to the first platform id
- [x] 3.3 In edit mode, render the device type as a disabled `Input` whose value is the resolved `display_name` for `self._existing.platform`
- [x] 3.4 Adjust `on_mount`/`_save` for the new layout (device type read-only on edit; IP/Name prefill unchanged; stored `platform` remains the id)
- [x] 3.5 Update `test_tui_devices.py`: assert cell order (device type → Name → IP), friendly labels shown in the dropdown, the stored value is the platform id, and edit shows a read-only, non-focusable device-type cell

## 4. Arrow-key navigation

- [x] 4.1 Add `up`/`down` bindings to `AddDeviceScreen` whose actions call `focus_previous()`/`focus_next()`; leave `left`/`right` unbound so inputs keep their text cursor
- [x] 4.2 Add `test_tui_devices.py` coverage: Down/Up move focus across the editable cells and the Save button

## 5. Save-button alignment

- [x] 5.1 In `app.py` CSS, give the Save button left padding so its left edge lines up with the cells above it; confirm the value against the live render

## 6. Preflight

- [x] 6.1 Format, lint, and run the full test suite; fix failures
- [x] 6.2 Drive the TUI and verify: cells ordered device type → Name → IP; dropdown shows friendly labels; edit shows a read-only device type; Up/Down navigate the cells and Save; Save is left-aligned with the cells
