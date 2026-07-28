## 1. Widen the action contract

Do this first: it is the only breaking edit, it touches existing tests, and every later
group builds on it. Each step should leave the suite green.

- [x] 1.1 Rename `ScriptResult` to `ActionResult` in `tui/actions.py` and update every
      reference in `tests/test_script_runner.py`, `test_script_results.py`,
      `test_run_script_modal.py`, and `test_action_catalog.py`. Run the suite.
- [x] 1.2 Add a frozen `ActionContext` dataclass to `tui/actions.py` carrying
      `remote_ip`, `session`, `notify`, `macros`, `custom_buttons`, `device_id`, and
      `platform`.
- [x] 1.3 Write a test asserting `run_action` passes an `ActionContext` to the catalog
      runner (red), then change `ActionType.runner` to
      `Callable[[dict, ActionContext], Awaitable[ActionResult]]`, adapt `run_script` to
      read `context.remote_ip`, and update `run_action`'s signature (green).
- [x] 1.4 Update `RemoteScreen._execute` to build an `ActionContext` and pass it to
      `run_action`. Run the suite; `test_custom_button_actions.py` and
      `test_tui_custom_button_config.py` must stay green.

## 2. Macro model and registry

Pure logic, no Textual. Mirrors how `tui/custom_buttons.py` keeps resolution out of the
store.

- [x] 2.1 Create `src/universal_remote/macros/models.py` with a `Macro` (stable `id`,
      `name`, ordered `steps`) and the four step shapes from design decision 7 —
      `key`, `text`, `action`, `pause` — plus `to_dict`/`from_dict` following
      `devices/models.py`.
- [x] 2.2 Write tests for a step's human-readable description (`Key: HOME`,
      `Pause: 500ms`, `Text: "…"`, and a captured action's own summary), then implement
      it. The detail modal and the playback modal both read this.
- [x] 2.3 Write tests for the registry: add, get by id, delete, list in saved order, and
      `next_number` advancing monotonically so a delete never lets a name be reused
      (spec: "Default macro names use a monotonic counter"). Then implement
      `macros/registry.py`.
- [x] 2.4 Write tests for draft operations — move a step up, move it down, no-op at the
      ends, delete, insert after an index — then implement them as pure functions over a
      step list.

## 3. Persistence

The chain has six links and one of them silently eats data. Complete it end to end.

- [x] 3.1 Add `macros: dict` to `Preferences`, a fault-tolerant branch in
      `PreferencesStore.load` (missing, malformed, or non-object → empty), and the
      `macros` key in `save`. Test round-trip plus malformed input.
- [x] 3.2 Add `self.macros: dict = {}` to `UniversalRemoteApp.__init__` and populate it
      from the loaded preferences in `on_mount`, alongside `custom_buttons`.
- [x] 3.3 **Add `macros=self.macros` to the `Preferences(...)` call in
      `persist_preferences`.** Write the guard test first: save a macro, change the
      theme, assert the macro survives. Without this, `watch_theme` erases every macro
      on any theme change.
- [x] 3.4 Test that theme, shortcuts, custom buttons, and macros all survive together
      across a restart, mirroring the existing "actions coexist" scenario.

## 4. Recording on the remote

- [x] 4.1 Write a test that the top row shows a fourth `Macros` button to the right of
      Back, then add it to `RemoteScreen.compose`.
- [x] 4.2 Write a test that entering the recording state does not make the remote scroll
      at the 80×45 baseline (mirroring
      `test_given_the_full_button_set_at_the_baseline_size_then_the_remote_does_not_scroll`),
      then add the recording state: a recording indicator label inside `#row-top` and the
      Macros button relabelled to `■ Stop` (append mode) or `■ Cancel` (capture-one
      mode). No new rows.
- [x] 4.3 Render the indicator's cancel hint from
      `display_label(effective_key("global.go_back", overrides))`. Test that rebinding
      Go Back changes the hint text.
- [x] 4.4 Write tests for capture at each tap point, then implement: a `key` step
      recorded in `_send` **after** a successful send (so an unsupported key and a
      failed send record nothing); a `text` step in the text-send path; an `action`
      snapshot in `_activate_custom` on the `if action:` branch only (so an
      edit-mode-armed or unconfigured button records nothing).
- [x] 4.5 Write a test that activating a `run_macro` custom button while recording runs
      it but records no step and reports that nested macros are unsupported, then
      implement the record-time refusal. This only needs to recognise the `"run_macro"`
      type *string* — the catalog entry itself does not exist until 8.6, so the test
      supplies the action dict directly.
- [x] 4.6 Write a test that the Go Back key while recording cancels the recording and
      leaves the session connected — it must not close the remote — then branch
      `action_go_back` on the recording state.

## 5. Macros list modal

- [x] 5.1 Write tests for the list modal: saved macros listed by name in saved order; a
      non-selectable "No macros yet" row when empty; Up/Down and `k`/`j` navigation
      (`j`/`k`, matching `_reserved_dpad`, not `k`/`l`); Close dismisses unchanged.
      Then implement `MacrosListModal`.
- [x] 5.2 Write a test that Create Macro **dismisses** the modal (does not leave it on
      the screen stack) and leaves the remote in append-mode recording, then implement
      it. A modal left on the stack freezes the remote via
      `Screen._modal_binding_chain` — this test is what catches that.
- [x] 5.3 Write tests for the return paths, then implement: `■ Stop` saves a new macro
      under its counter name and reopens the list with it selected; Go Back reopens the
      list unchanged; stopping with zero steps creates nothing and reports it.
- [x] 5.4 Write a test that Enter on a macro row opens its detail modal, then wire it.

## 6. Macro detail modal

- [x] 6.1 Write tests for the draft: the modal renders from an in-memory draft, not the
      persisted macro; Save persists name and steps; Close discards every edit; Delete
      removes the macro. Then implement `MacroDetailModal`.
- [x] 6.2 Lay out the controls as two rows of buttons with `min-width: 0` and explicit
      widths (Textual's default `min-width: 16` × 7 buttons overflows 80 columns — see
      the existing `#button-config-buttons Button` rule). Test that the modal fits and
      scrolls its step list rather than clipping its buttons on a short terminal.
- [x] 6.3 Write tests for the step controls — move up, move down, no-op at the ends,
      delete — asserting each changes only the draft (Close afterwards leaves the macro
      untouched). Then wire them to the group 2.4 functions.
- [x] 6.4 Write tests for add-step, then implement: it dismisses the detail modal, puts
      the remote in capture-one recording, and on one captured interaction re-pushes the
      detail modal **carrying the same draft** with the step inserted after the selected
      one. Include the regression test that a rename plus a reorder made before
      add-step survives the round trip.
- [x] 6.5 Write a test that Go Back or `■ Cancel` during capture-one returns to the
      detail modal with the draft unchanged, then implement it.

## 7. Pause steps

- [x] 7.1 Write tests for the pause prompt: a valid millisecond value inserts a pause
      after the selected step; cancel inserts nothing; a negative, fractional, or
      non-numeric value inserts nothing. Then implement the prompt modal.
- [x] 7.2 Write a test that opening an existing pause step reopens the prompt prefilled
      with its current value and that a new value replaces it, then implement it.

## 8. Playback

- [x] 8.1 Write tests for the playback modal: it names the macro, reports progress
      (`Step 3 of 12`), dismisses itself when the last step completes, and that a remote
      keyboard shortcut pressed while it is open sends nothing. Then implement
      `MacroPlaybackModal`, starting its step loop in `on_mount`.
- [x] 8.2 Implement the step loop: `key` → `session.send_key`, `text` →
      `session.send_text`, `pause` → sleep for its duration, `action` → `run_action`
      **directly**. Write the regression test first, in both variants: a macro holding a
      captured script step with `show_results: true` must not present a result modal
      during playback whether that step succeeds (playback continues) or fails (the run
      aborts). Never reuse `RemoteScreen._execute`, which calls `present_result`.
- [x] 8.3 Write tests for abort-on-failure — an unsupported key, a failed send, a non-zero
      script exit — each dismissing the modal, running no later step, and raising an error
      notification naming the macro, the failing step, and the reason, with the returned
      result unsuccessful. Include the complement: a run whose every step succeeds returns
      a successful result summarising how many steps ran. Then implement it.
- [x] 8.4 Write a test that a nested `run_macro` step is refused, reported, and aborts the
      run rather than recursing, then implement the depth guard.
- [x] 8.5 Write a test that Cancel and the Go Back key each stop playback at the current
      step and dismiss the modal, with no further steps sent, an unsuccessful result naming
      that step, and **no** error notification. Then implement it.
- [x] 8.5a Add `reports_own_outcome: bool = False` to `ActionType`, set it on the
      `run_macro` entry, and skip `present_result` in `RemoteScreen._execute` for a type
      that declares it. Write the test first: an aborted or cancelled macro must raise no
      `"Script failed"` toast on top of the modal's own reporting, since `present_result`
      toasts any not-ok result under that title. `run_script` keeps its current path.
- [x] 8.6 Add the `run_macro` catalog entry whose runner resolves the macro id from
      `context.macros` and awaits `app.push_screen_wait(MacroPlaybackModal(...))`. Test
      that a button pointing at a deleted macro reports the macro is missing and sends
      nothing.

## 9. Run Macro configuration

- [x] 9.1 Write tests for the macro picker: it lists saved macros by name; confirming
      stores an action referring to the macro **by id**; Cancel stores nothing; it states
      there are none when the registry is empty; it offers no results toggle. Then
      implement `RunMacroConfigModal`.
- [x] 9.2 Write a test that reopening the configuration for a button that already has a
      Run Macro action preselects the referenced macro, then implement the prefill.
- [x] 9.3 Write a test that renaming or editing an assigned macro changes what the button
      does (proving the action holds an id, not a copy).

## 10. Documentation and preflight

- [x] 10.1 Document macros in the user-facing docs: recording, editing, assigning one to
      a custom button, and the deliberate limitations (no nesting, no loops, snapshotted
      button steps, no undo of a partial run).
- [x] 10.2 Update `tests/test_shortcuts_catalog.py` for the Remote action count (thirty-one
      → thirty-two) and assert the new action has no default key, then register a
      `remote.macros` action in the keyboard-shortcuts catalog with `show=False`, so the
      Macros control can be given a shortcut without adding a footer hint the 80-column
      footer cannot fit. Consider doing this alongside 4.1 rather than last, since the
      catalog test will fail as soon as the count changes.
- [x] 10.3 Preflight: run the formatter, fix all lint findings, and run the full suite.
- [ ] 10.4 Verify against the specs by hand on a real device — record a macro, edit it,
      assign it to a custom button, play it, and cancel a play mid-run.
