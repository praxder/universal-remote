## 1. Store reorder (red → green)

- [x] 1.1 In `tests/test_store.py`, add failing tests for `DeviceStore.move_up` / `move_down`: moving the second device up swaps it with the first, moving the first down swaps it with the second, and other devices keep their positions
- [x] 1.2 Add a failing test that the moved order is returned after re-reading the store from disk
- [x] 1.3 Add failing tests for the no-op cases: first device up, last device down, and an unknown device id — each leaves the stored order unchanged when the store is read back. Assert on the order only; do not spy on `save_all` or compare file mtimes (see design.md)
- [x] 1.4 Add a failing test that a moved device keeps its name, platform, IP, credential, and reconnection identifier
- [x] 1.5 Implement `move_up(device_id)` and `move_down(device_id)` in `src/universal_remote/devices/store.py` over one private swap helper that returns early on an unknown id or an out-of-range target index, and otherwise swaps and calls `save_all`
- [x] 1.6 Confirm 1.1–1.4 pass

## 2. Order guarantees already relied on (regression cover)

- [x] 2.1 In `tests/test_device_crud.py` (or `test_store.py`, wherever add/delete are covered), add tests that adding appends last, editing keeps position, and deleting preserves the relative order of the rest — the guarantees the new "List devices" requirement states

## 3. Manage Devices screen (red → green)

- [x] 3.1 In `tests/test_tui_devices.py`, add a failing test that Move Up and Move Down buttons are present and enabled below the device list
- [x] 3.2 Add failing tests that activating Move Down on the first device reorders and renumbers the rows, and that activating Move Up on the second device does the mirror image
- [x] 3.3 Add failing tests that `shift+down` / `shift+up` and the `J` / `K` aliases on the list do the same as the matching buttons
- [x] 3.4 Add a failing test that the highlight follows the moved device: highlight the first of three, move it down twice, assert it is row three *and* is the highlighted row
- [x] 3.5 Add a failing test that focus is on the device list after a move activated from a button
- [x] 3.6 Add failing tests for the silent no-ops: first device up, last device down, and a move while the `+ Add` row is highlighted — the listed order and the store are unchanged
- [x] 3.7 Change `_reload()` to `_reload(select_id: str | None = None)`: highlight the index of the device with that id when given, else keep the existing `highlighted = 0`. Leave the `action_delete` and `on_screen_resume` calls as they are
- [x] 3.8 Add the button row to `compose` (a horizontal container below `#device-list`, inside `#devices`) and handle `Button.Pressed` for the two ids
- [x] 3.9 Add `action_move_up` / `action_move_down`: guard on `_selected()` returning `None`, call the store, `_reload(select_id=device.id)`, then focus the list. Bind `shift+up` / `shift+down` plus the `K` / `J` aliases (`show=False`) on `DeviceListScreen.BINDINGS` — **not** on `DeviceOptionList`, which the Use Remote picker shares
- [x] 3.10 Add CSS in `tui/app.py` for the button row; set `min-width: 0` alongside any width below 16, and `border: none` on `#device-list` if it renders blank
- [x] 3.11 Confirm 3.1–3.6 pass

## 4. Propagation to Use Remote

- [x] 4.1 In `tests/test_tui_remote_flow.py`, add a test that the picker lists devices in the stored order with matching numbering after a reorder
- [x] 4.2 Add a test that a digit key selects the device now at that position after a reorder

## 5. Visual verification at 80×24

- [x] 5.1 Run the app at an 80×24 terminal, export a screenshot of Manage Devices, convert it to PNG, and look at it: the device list must still render its rows, the button row must be fully visible, and neither button label may clip
- [x] 5.2 Check the Footer at 80 columns — with the two new hints it shows six plus the palette hint; if anything clips, mark the new bindings `show=False`

## 6. Documentation

- [x] 6.1 Update the README's "Manage your devices" section (README.md:79) to mention reordering by the two buttons and by `shift+up` / `shift+down`, and that the order drives the Use Remote picker and the `1`–`9` shortcuts
- [ ] 6.2 Regenerate `docs/screenshots/device-list.png` — it shows the list without the button row
  - **Blocked:** the twelve sibling assets are real terminal captures, and `screencapture` returns a black
    frame here (no Screen Recording permission for this process). An `export_screenshot` SVG render would
    not match their font or chrome. Recipe: `XDG_CONFIG_HOME=<tmp>` with a seeded six-device `devices.json`,
    run `uv run universal-remote` in iTerm at 80x28, press `d`, capture the content area (~842px wide).

## 7. Preflight

- [x] 7.1 `uv run ruff format`
- [x] 7.2 `uv run ruff check` and fix anything reported
- [x] 7.3 `uv run pytest` — full suite green
- [x] 7.4 `openspec validate reorder-device-list --strict`
