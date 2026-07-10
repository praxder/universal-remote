## Why

The Manage Devices screen labels itself with a plain "Manage Devices" text and hides Add behind a keypress (`a`). Two problems: the screen doesn't match the menu's ASCII-banner style, and on first run — when no devices exist — the primary action (Add) is invisible. Surfacing Add as an always-present last row makes it discoverable, and a "Devices" banner matches `MenuScreen`'s `TITLE_ART`.

## What Changes

- Replace the static `Label("Manage Devices")` with a "Devices" ASCII-art banner, rendered as a `Static` like the menu's `TITLE_ART`.
- Add an always-present "add" entry as the **last row** of the device list (an `OptionList` option with a sentinel id).
- With one or more saved devices: list the devices first, then a `Separator`, then the add row. On first run (no devices): the list shows **only** the add row, and the separate `#devices-empty` hint label is removed.
- Selecting the add row — by Enter or mouse click — opens the add flow.
- Selecting a device row — by Enter or mouse click — opens that device for editing, equivalent to the existing edit action.
- The `a` (add), `e` (edit), and `delete` key bindings are retained for keyboard parity.

## Capabilities

### New Capabilities
<!-- none -->

### Modified Capabilities
- `tui-remote`: The "Device management screens" requirement is updated — a "Devices" ASCII banner, an always-present add row as the last row (devices then a separator then add when any exist; add-only on first run), and Enter/click selection that edits a device or opens the add flow.

## Impact

- **Code**: `src/universal_remote/tui/devices_screen.py` (banner `Static`; rebuild the list in `_reload()` with device options, a `Separator` when devices exist, then an add `Option` sentinel; add `on_option_list_option_selected`; drop the `#devices-empty` label), `src/universal_remote/tui/app.py` (banner-width CSS for `#devices-title`).
- **Tests**: `tests/test_tui_devices.py` (first-run shows only the add row; devices then separator then add; click and Enter on the add row open `AddDeviceScreen`; click and Enter on a device row open the edit flow).
- **Dependencies**: none — the divider between devices and the add row uses `OptionList.add_option(None)`, built into Textual.
