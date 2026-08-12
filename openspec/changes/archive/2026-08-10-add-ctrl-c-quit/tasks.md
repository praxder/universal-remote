## 1. Quit binding (red → green)

- [x] 1.1 Add failing TUI tests that press `ctrl+c` and assert the app exits: inside the shortcut capture modal (the only place that traps every key), with an `Input` focused on the Add Device screen, on the device list screen, and on the entry menu
- [x] 1.2 Add a test that `ctrl+q` still quits
- [x] 1.3 Add `BINDINGS = [Binding("ctrl+c", "quit", "Quit", show=False, priority=True)]` to `UniversalRemoteApp` with a comment recording why `priority=True` is required
- [x] 1.4 Confirm the new tests pass and no footer-hint test regresses (the binding is `show=False`)

## 2. Reserved quit keys in the catalog

- [x] 2.1 Add failing catalog tests: a `framework.quit` entry on `ctrl+c` with `ctrl+q` as a fixed alias, `editable=False`, `target=None`, and `is_reserved` true for both keys
- [x] 2.2 Add a failing test that `without_reserved` drops a saved override bound to `ctrl+c`
- [x] 2.3 Add the reserved framework entry to `CATALOG`, matching the shape of `framework.command_palette` plus the D-pad rows' alias handling
- [x] 2.4 Confirm the Keyboard Shortcuts table shows it as one disabled `CTRL-C / CTRL-Q` row and that no existing catalog or shortcuts-screen test regresses

## 3. Release the device session on quit

- [x] 3.1 Reproduce the leak end-to-end: drive the real app with an adapter whose session owns a live `aiohttp.ClientSession`, quit from the remote, and confirm the process prints `Unclosed client session` after exit
- [x] 3.2 Add a failing test that quitting from the remote with Ctrl+C closes the device session (asserted after shutdown, where teardown runs)
- [x] 3.3 Close the session from `RemoteScreen.on_unmount` so every teardown route releases it; `BaseSession.close()` is already idempotent, so Go Back still closes exactly once
- [x] 3.4 Move the text-modal test's session assertions inside the run — they ran after shutdown and only passed because nothing used to close the session there
- [x] 3.5 Re-run the reproduction and confirm the warning is gone
- [x] 3.6 Probe the failure modes of that release: a close that raises printed a traceback after exit, and a close that hung delayed the exit by its full duration — both run outside the app's error net
- [x] 3.7 Bound the release with `CLOSE_TIMEOUT` and log rather than raise, then add tests for a raising close, a hanging close, and quitting from a modal over the remote (`close_error` / `close_delay` on `FakeSession`)

## 4. Documentation

- [x] 4.1 README: add `Ctrl+C`/`Ctrl+Q` to the reserved-keys list and a "Quit from anywhere" bullet noting that Ctrl+C no longer copies in a text field and terminal copy still does
- [x] 4.2 Recapture `docs/screenshots/shortcuts.png` and `docs/screenshots/shortcuts-palette.png` — both are built by `_populate_shortcuts_table`, so both now show a table missing the Quit (Any Screen) row (must be captured from the running app by hand; an `export_screenshot` render would not match the sibling assets' chrome — see `openspec/changes/archive/2026-07-31-reorder-device-list/tasks.md:41-44`)

## 5. Preflight and verification

- [x] 5.1 Run the formatter and linter
- [x] 5.2 Run the full test suite
- [x] 5.3 Real-terminal check: run the app under a pty, write `\x03` from the entry menu, and confirm the process exits with no toast
- [x] 5.4 Real-terminal check: repeat with the Add Device name `Input` focused, and confirm `ctrl+q` still quits
- [x] 5.5 Visually confirm the `CTRL-C / CTRL-Q` disabled row on the Keyboard Shortcuts screen
- [x] 5.6 `openspec validate add-ctrl-c-quit --strict`
