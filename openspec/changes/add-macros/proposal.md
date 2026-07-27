## Why

People who use the remote hit the same sequences over and over — logging into a
streaming app, navigating to a buried settings screen, running a test sequence. Every
one of those is a hand-typed run of keys the user already knows by heart, retyped every
time. A macro records that sequence once, names it, and replays it.

The pieces to build on already exist: the remote funnels every key press (click *and*
hotkey) through a single choke point, and the custom-button action catalog was
explicitly designed so a new action type slots in without reworking the remote surface.
Macros are the first real payoff on that extensibility.

## What Changes

- **New `macros` capability.** A macro is a named, persisted, ordered list of steps —
  device keys, text sends, snapshotted custom-button actions, and explicit pauses —
  with its own identity, so anything can invoke it.
- **Macros modal on the remote.** A fourth top-row button, `Macros`, opens a list of
  saved macros. The list is navigable by arrow keys and by `j`/`k`, offers Create Macro
  and Close, and shows a non-selectable "No macros yet" row when empty.
- **Recording mode on the remote.** Create Macro dismisses the modal, returns to the
  live remote, and records every key press, text send, and custom-button action until
  the user stops. The recording indicator and Stop control reuse the top row, so
  recording adds **zero rows** to the remote's height.
- **Macro detail modal.** Rename the macro, reorder steps, delete a step, record one
  additional step, insert a pause with a millisecond value, then Save, Close, or Delete
  the whole macro. Edits live in an in-memory draft; only Save writes.
- **Playback via a new `run_macro` action type.** A custom button can be assigned
  `Run Macro` and pointed at a macro by id. Playback shows a blocking modal with
  progress and Cancel, so the remote is frozen while a macro runs. A failed step aborts
  the run: the remaining steps do not run, the modal dismisses, and an error notification
  names the macro, the step it stopped at, and why.
- **BREAKING (internal):** the action-catalog runner signature widens from
  `(action, remote_ip)` to `(action, context)`. Macro playback needs the live session,
  the notifier, and the custom-button map — none of which fit the current two-argument
  shape. One call site; `run_script` reads only `context.remote_ip`.
- **BREAKING (internal):** `ScriptResult` is renamed `ActionResult`, since it is now the
  return type of every catalog action rather than only Run Custom Script.
- Nested macros are refused: a macro step that would invoke another macro is rejected at
  record time with a message, and a depth guard rejects it at playback for hand-edited
  data, aborting the run like any other failed step.

## Capabilities

### New Capabilities
- `macros`: recording, editing, persisting, and replaying named sequences of remote
  actions, including the macros list and detail modals, the recording mode, the step
  model, and the blocking playback modal.

### Modified Capabilities
- `tui-remote`: the on-screen remote surface gains a fourth top-row button (`Macros`)
  and a recording state in which that button becomes the Stop/Cancel control and a
  recording indicator is shown; Escape on the remote cancels recording instead of
  leaving the remote while a recording is in progress.
- `custom-button-actions`: the action catalog gains a second type, `Run Macro`, and the
  catalog's runner contract widens from an IP string to an execution context so an
  action can reach the live session. Run Custom Script's own execution is unchanged, but
  its Results choice is now scoped to a direct button activation — a captured script step
  never presents a result modal mid-playback.
- `keyboard-shortcuts`: the catalog enumerates its Remote actions exhaustively
  ("thirty-one rebindable actions"), so adding a Macros action makes it thirty-two. The
  new action defaults to no shortcut and stays out of the footer, matching how the twelve
  formerly mouse-only keys are handled.
- `app-preferences`: a new persisted `macros` field holds the macro registry and the
  default-name counter, alongside the existing theme, shortcuts, and custom buttons,
  with the same fault-tolerant read/write behavior.

## Impact

**New code**
- `src/universal_remote/macros/` — the macro model, the registry, and the step types.
- Macros list modal, macro detail modal, pause-entry modal, playback modal (TUI).

**Modified code**
- `tui/actions.py` — `ActionContext`, widened `ActionType.runner`, `ActionResult`
  rename, `run_macro` catalog entry and runner.
- `tui/remote_screen.py` — fourth top-row button; recording state threaded through
  `_send`, `_activate_custom`, and the text-send path; `action_go_back` branches while
  recording.
- `preferences/store.py` — `Preferences.macros` field, load branch, save key.
- `tui/shortcuts.py` — a `remote.macros` catalog entry, no default key, `show=False`.
- `tui/app.py` — `macros` attribute, `on_mount` population, and `persist_preferences`
  (which rebuilds `Preferences` from explicit keyword arguments — omitting `macros`
  there would let any theme change silently erase every macro).

**Tests**
- `tests/test_script_runner.py`, `test_script_results.py`, `test_run_script_modal.py`,
  `test_action_catalog.py` — updated for the renamed result type and widened runner.
- New suites for the macro registry, recording, the detail modal, and playback.

**No change**
- Adapters, the session protocol, `Key`, device discovery, and reachability are
  untouched. Macros compose existing send paths and add no new device capability.
