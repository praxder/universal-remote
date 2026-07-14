## 1. Numbered device lists + digit selection

- [ ] 1.1 Add a failing test in `tests/test_tui_devices.py`: opening Manage Devices with saved devices shows rows prefixed `1. `, `2. `… and the `+ Add` row unprefixed.
- [ ] 1.2 Add a failing test in `tests/test_tui_remote_flow.py`: the Use Remote picker shows device rows prefixed `1. `, `2. `…
- [ ] 1.3 Add failing tests: pressing a digit opens the Nth device (edit flow on Manage Devices, connect/pair flow on Use Remote), and an out-of-range digit is a no-op.
- [ ] 1.4 Create a shared `OptionList` subclass (e.g. in `src/universal_remote/tui/`) that owns digit-key handling: on `1`–`9`, map to option index `N-1`, guard `idx < device_count and option is not None and option.id != ADD_ID`, set `highlighted` and invoke the select action.
- [ ] 1.5 Use the subclass in `DeviceListScreen` and `UseRemoteScreen`; build rows as `Option(f"{i + 1}. {device.name}", id=device.id)` so `id` stays the raw device id.
- [ ] 1.6 Run the tests from 1.1–1.3 green.

## 2. Vim-style menu and list navigation

- [ ] 2.1 Add a failing test in `tests/test_tui_menu.py`: `j`/`k` move focus between the two mode buttons like Down/Up.
- [ ] 2.2 Add failing tests: `j`/`k` move the highlight in both device lists; `h`/`j`/`k`/`l` move focus in the delete-confirmation dialog.
- [ ] 2.3 Add a failing test: typing `h`/`j`/`k`/`l` into the add/edit form's Name input enters the characters and does not move focus.
- [ ] 2.4 Bind `k`/`h`→previous and `j`/`l`→next on `MenuScreen` and `ConfirmDeleteScreen`, aliasing the existing focus actions, all `show=False`.
- [ ] 2.5 Add `j`→`cursor_down` and `k`→`cursor_up` bindings (`show=False`) to the shared `OptionList` subclass from task 1.4.
- [ ] 2.6 Confirm the add/edit form is left unchanged (arrows only) and run the tests from 2.1–2.3 green.

## 3. Remote D-pad Vim keys + Home on Space

- [ ] 3.1 Add failing tests in `tests/test_tui_remote_surface.py`: `h`/`j`/`k`/`l` send LEFT/DOWN/UP/RIGHT, and Space sends HOME.
- [ ] 3.2 In `RemoteScreen.BINDINGS`, add `h`/`j`/`k`/`l` → `send('LEFT'|'DOWN'|'UP'|'RIGHT')` alongside the arrows.
- [ ] 3.3 Replace the `h`→`send('HOME')` binding with `space`→`send('HOME')`.
- [ ] 3.4 Run the tests from 3.1 green; confirm the existing arrow/OK/Back/text tests still pass.

## 4. Docs + preflight

- [ ] 4.1 Update `README.md` if it documents key bindings.
- [ ] 4.2 Run formatter, linter, and the full test suite; fix any failures.
- [ ] 4.3 Manually exercise the app: numbered rows, digit selection, `hjkl` on menus/lists, and remote `hjkl` + Space=Home.
