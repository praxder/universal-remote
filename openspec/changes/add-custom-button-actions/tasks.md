## 1. Prerequisite

- [x] 1.1 Confirm Phase 1 (`add-custom-remote-buttons`) is implemented and archived so the custom-button row, Button Config modal, and `custom_buttons` persistence exist in the live code and specs

## 2. Persistence: action stored in the custom-button entry

- [ ] 2.1 Write failing tests: an `action` object round-trips inside a button's per-scope entry; a title-only entry loads with no action (back-compat); saving an action leaves theme, shortcuts, and titles untouched
- [ ] 2.2 Extend the custom-button entry model and store read/write to carry an optional `action` object alongside the title
- [ ] 2.3 Write failing tests for action resolution: most-specific-first (device → type → global) and independent of title resolution
- [ ] 2.4 Add action resolution to the custom-button resolver, resolving the action separately from the title

## 3. Action catalog and Action Type list modal

- [ ] 3.1 Write failing tests: the catalog exposes one action type (`run_script` → "Run Custom Script"); the `ActionTypeListModal` lists it and selecting it opens the Run Script config modal
- [ ] 3.2 Implement the extensible action catalog (id, label, config modal, runner per action type) with the single `run_script` entry
- [ ] 3.3 Implement `ActionTypeListModal` driven by the catalog

## 4. Run Script config modal

- [ ] 4.1 Write failing tests: source toggle (file → one-line path input; inline → multi-line editor), Results toggle (Don't Show / Show), the `REMOTE_IP` helpline, OK stores the action, Cancel stores nothing
- [ ] 4.2 Implement `RunScriptConfigModal` (source toggle, path input / `TextArea`, Results toggle, helpline, OK/Cancel)
- [ ] 4.3 On OK, store the configured action (source kind, script/path, results choice) on the button at the scope chosen in the Button Config modal

## 5. Script execution engine

- [ ] 5.1 Write failing tests: execution is non-blocking; `REMOTE_IP` is set in the environment to the device IP; the timeout terminates a hung script and marks it failed; an unstartable path fails without crashing
- [ ] 5.2 Implement the executor module — background worker + asyncio subprocess, `REMOTE_IP` env injection, bounded timeout, exit-code/output capture
- [ ] 5.3 Write failing tests for results visibility: Don't Show → silent success, error toast on failure; Show → result modal on success and failure with output and exit code
- [ ] 5.4 Implement the result modal and error-toast wiring keyed off the action's Results choice

## 6. Remote wiring: run-vs-config and edit gesture

- [ ] 6.1 Write failing tests: clicking a button with a resolved action runs it; clicking a button with no action opens config; the edit gesture opens config for a button that has an action
- [ ] 6.2 Activate the Action Type control in the Button Config modal and wire it through the Action Type list → Run Script config → action storage
- [ ] 6.3 Implement custom-button click dispatch (run when an action resolves, else open config) and the edit gesture that opens config for a configured button (resolve the exact edit-mode binding; avoid reserved keys)
- [ ] 6.4 Thread the connected device's IP from `app.py`/the remote screen to the executor

## 7. Docs, trust model, and preflight

- [ ] 7.1 Document the trust model in the repo docs/README: user-authored shell runs unsandboxed on the user's machine, `REMOTE_IP` is the only injected value, and the timeout is a reliability guard, not a security control
- [ ] 7.2 Update in-repo docs for custom-button actions (assigning Run Custom Script, file vs inline, results visibility)
- [ ] 7.3 Run the formatter and linter; fix all warnings
- [ ] 7.4 Run the full test suite and fix any failures
- [ ] 7.5 Before archiving: reconcile the two `tui-remote` MODIFIED scenarios the archive drop-guard will flag (they change scenarios Phase 1 put in the live specs). "Clicking a custom button opens its configuration" → keep that live header, narrow its WHEN to the no-action case, and add "Clicking a button with an action runs it". "Action Type is a disabled placeholder" → a genuine flip to active with no truthful in-place edit; MODIFIED can't express a single-scenario removal, so decide the mechanism at archive time (last resort `openspec archive --no-validate`)
