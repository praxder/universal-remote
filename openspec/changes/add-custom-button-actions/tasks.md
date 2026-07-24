## 1. Prerequisite

- [x] 1.1 Confirm Phase 1 (`add-custom-remote-buttons`) is implemented and archived so the custom-button row, Button Config modal, and `custom_buttons` persistence exist in the live code and specs

## 2. Persistence: action stored in the custom-button entry

- [x] 2.1 Write failing tests: an `action` object round-trips inside a button's per-scope entry; a title-only entry loads with no action (back-compat); saving an action leaves theme, shortcuts, and titles untouched
- [x] 2.2 Extend the custom-button entry model and store read/write to carry an optional `action` object alongside the title
- [x] 2.3 Write failing tests for action resolution: the entry resolves as a unit, most-specific-first (device → type → global), so title and action always come from the same scope
- [x] 2.4 Add action resolution to the custom-button resolver, resolving the entry as a unit so the action comes from the same scope as the title

## 3. Action catalog and Action Type list modal

- [x] 3.1 Write failing tests: the catalog exposes one action type (`run_script` → "Run Custom Script"); the `ActionTypeListModal` lists it and selecting it opens the Run Script config modal
- [x] 3.2 Implement the extensible action catalog (id, label, config modal, runner per action type) with the single `run_script` entry
- [x] 3.3 Implement `ActionTypeListModal` driven by the catalog

## 4. Run Script config modal

- [x] 4.1 Write failing tests: source toggle (file → one-line path input; inline → multi-line editor), Results toggle (Don't Show / Show), the `REMOTE_IP` helpline, OK stores the action, Cancel stores nothing
- [x] 4.2 Implement `RunScriptConfigModal` (source toggle, path input / `TextArea`, Results toggle, helpline, OK/Cancel)
- [x] 4.3 On OK, store the configured action (source kind, script/path, results choice) on the button at the scope chosen in the Button Config modal

## 5. Script execution engine

- [x] 5.1 Write failing tests: execution is non-blocking; `REMOTE_IP` is set in the environment to the device IP; the timeout terminates a hung script and marks it failed; an unstartable path fails without crashing
- [x] 5.2 Implement the executor module — background worker + asyncio subprocess (`/bin/sh -c` for inline scripts, the given path for file scripts), `REMOTE_IP` env injection, a fixed 30-second timeout, exit-code/output capture
- [x] 5.3 Write failing tests for results visibility: Don't Show → silent success, error toast on failure; Show → result modal on success and failure with output and exit code
- [x] 5.4 Implement the result modal (scrollable, showing the full untruncated stdout/stderr plus exit code) and error-toast wiring keyed off the action's Results choice

## 6. Remote wiring: run-vs-config and edit gesture

- [x] 6.1 Write failing tests: clicking a button with a resolved action runs it; clicking a button with no action opens config; with edit-mode armed, the next activation (click or shortcut) opens config for a button that has an action and then clears edit-mode
- [x] 6.2 Activate the Action Type control in the Button Config modal and wire it through the Action Type list → Run Script config → action storage
- [x] 6.3 Implement custom-button click dispatch (run when an action resolves, else open config) and the edit-mode key that arms edit-mode so the next custom-button activation (click or shortcut) opens config and then clears the mode (pick a non-reserved keycap from the remote key map)
- [x] 6.4 Thread the connected device's IP from `app.py`/the remote screen to the executor

## 7. Docs, trust model, and preflight

- [x] 7.1 Document the trust model in the repo docs/README: user-authored shell runs unsandboxed on the user's machine, `REMOTE_IP` is the only injected value, and the timeout is a reliability guard, not a security control
- [x] 7.2 Update in-repo docs for custom-button actions (assigning Run Custom Script, file vs inline, results visibility)
- [x] 7.3 Run the formatter and linter; fix all warnings
- [x] 7.4 Run the full test suite and fix any failures (all feature tests pass; the sole failure, `test_tui_menu.py::…use_remote_is_clicked`, is a pre-existing mount-timing flake unrelated to this change — reproduced on a clean branch HEAD with all changes stashed)
- [ ] 7.5 Before archiving: reconcile the two `tui-remote` MODIFIED scenarios the archive drop-guard will flag (they change scenarios Phase 1 put in the live specs). "Clicking a custom button opens its configuration" → keep that live header, narrow its WHEN to the no-action case, and add "Clicking a button with an action runs it". "Action Type is a disabled placeholder" → a genuine flip to active with no truthful in-place edit; MODIFIED can't express a single-scenario removal, so decide the mechanism at archive time (last resort `openspec archive --no-validate`)

## 8. First-pass review refinements

- [x] 8.1 Reset control: add a Reset button to the Button Config modal that clears the button's title and action at every scope for the active device (default title, no action), persists, and closes — with a test and the `tui-remote` scope
- [x] 8.2 Scope save takes effect: on OK, drop the button's entry at any scope more specific than the selected scope (for the active device/type) so the chosen scope resolves, fixing "setting Global/Device Type does not take effect" — with unit + modal tests and the `tui-remote` scope
- [x] 8.3 Edit-mode key reliability: drop saved shortcut overrides whose key is now reserved (e.g. a pre-reservation `e→Stop` override that shadowed edit-mode) on load and re-persist, so pressing `e` arms edit-mode — with unit, load, and end-to-end tests and a new `keyboard-shortcuts` delta (`e` reserved, drop-on-load)
- [x] 8.4 Edit-mode visual indicator: the custom buttons show a warning-colored bold border while edit-mode is armed, clearing when it ends — with a test and the `tui-remote` scope
- [x] 8.5 Run Script file source: run a script file through the shell (`/bin/sh <path>`, `~` expanded) so it needs no exec bit or shebang, and report a non-existent path as a clean start failure — fixes "Exec format error" — with tests and the `custom-button-actions` scope
- [x] 8.6 Result modal: center the Close button (presentation only; no spec change) — with a geometry test
