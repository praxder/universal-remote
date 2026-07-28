## Context

The remote surface funnels every key press through one place. `RemoteScreen._send(key)`
is reached by a mouse click on a button and by a rebindable hotkey alike, and
`action_send` already early-returns on an unsupported key *before* reaching it. That
single choke point is what makes recording tractable: one hook captures both input
methods and never captures a press that did not actually happen.

The action catalog (`tui/actions.py`) was built to be extended — its docstring and the
`ACTION_CATALOG` comment both say adding a type should not touch the remote surface or
the Button Config modal. It currently holds exactly one type, `run_script`, whose runner
signature is `Callable[[dict, str], Awaitable[ScriptResult]]`: an action dict and the
device IP.

Constraints that shape the design:

- **The remote's vertical budget is spent.** The supported baseline is 80×45
  (`tests/test_tui_remote_surface.py:17`) and the rendered remote is roughly 40 rows.
  `test_given_the_full_button_set_at_the_baseline_size_then_the_remote_does_not_scroll`
  pins that. A recording banner row plus a Stop Recording button row is about five
  rows — it would pass at exactly the baseline with zero slack.
- **The footer is at capacity.** `remote_screen.py` already keeps Go Back out of the
  footer because "a ninth hint does not fit the supported 80-column width."
- **A modal freezes the screens below it.** Textual's `Screen._modal_binding_chain`
  (`screen.py:449-455`) truncates the binding chain at the last modal, so a
  `ModalScreen` on the stack stops the remote's bindings from firing.
- **`App.push_screen_wait` exists** (`app.py:2981`) and is awaitable from a worker.
  `RemoteScreen._run_action` already runs its action in a worker.
- **Escape is rebindable.** `global.go_back` is an editable catalog entry, so any
  on-screen text naming Escape must be derived, not hardcoded.

## Goals / Non-Goals

**Goals:**

- Record a sequence of remote interactions — keys (click or hotkey), text sends, and
  custom-button actions — with one hook per input path.
- Persist macros across runs with their own identity, so invokers reference a macro
  rather than embedding it.
- Replay a macro with the remote frozen, showing progress and offering cancellation.
- Make a macro editable after recording: rename, reorder, delete, append, insert pauses.
- Add recording UI without growing the remote's height.

**Non-Goals:**

- **Nested macros.** A macro invoking another macro is refused, not supported.
- **Conditional or looping steps.** A macro is a flat, linear list.
- **Macro scoping.** The registry is flat and global. Scoping comes free from the custom
  button that invokes it, which is already layered device/type/global.
- **Timing fidelity.** Recording does not capture the wall-clock gaps between presses. A
  macro paces itself with one editable default gap between steps (Decision 14), plus
  explicit pause steps the user adds where a longer wait matters.
- **Undo of a partially played macro.** Keys already sent stay sent.
- **New invocation surfaces beyond a custom button.** The macro's stable id makes a
  hotkey or CLI trigger straightforward later; neither is in this change.

## Decisions

### 1. Playback is a catalog action type, not a bespoke remote path

`run_macro` becomes the catalog's second entry. A custom button holds
`{"type": "run_macro", "macro_id": "<id>"}` and its config modal is a picker over saved
macros.

*Why:* the extensibility the catalog already promises. `_activate_custom` needs no
change — it resolves an action and runs it, whatever the type. Custom buttons also
already carry an optional user-assignable hotkey (`remote.custom_N`), so macros get
keyboard invocation for free.

*Alternative rejected:* special-casing `run_macro` inside `_activate_custom`. Fewer
lines now, but it breaks the catalog contract the codebase already paid for and would
make a third action type harder, not easier.

### 2. The macro is referenced by id, never embedded in the button

A flat registry keyed by opaque id holds the macros; the button holds only the id.

*Why:* one macro, many invokers. A later hotkey, CLI trigger, or list-modal Play button
all point at the same object, and editing the macro changes every invoker at once.
Embedding the macro in the button would fork it per invoker.

*Consequence:* a button pointing at a deleted macro is a dangling reference. Playback
resolves it and reports "That macro no longer exists" rather than crashing.

### 3. The runner signature widens to a context object

```
ActionType.runner: Callable[[dict, ActionContext], Awaitable[ActionResult]]

ActionContext(app, remote_ip, session, macros, custom_buttons, device_id, platform)
```

`run_script` reads only `remote_ip`. `run_macro` needs the `app` (to push its playback
modal — a module-level runner has no other route to `push_screen_wait` — and to raise
the abort notification), the live `session` (to send keys and text), `macros` (to
resolve the id), and `custom_buttons` + `device_id` + `platform` (unused today, but a
future step type that resolves a button would need them).

*Why:* macro playback fundamentally needs the session, and an IP string cannot carry it.
There is exactly one `run_action` call site (`remote_screen.py:509`), so the widening is
cheap.

*Alternative rejected:* threading extra positional parameters. Each new action type
would widen the signature again and every runner would have to accept parameters it
ignores. A frozen context dataclass grows without touching existing runners.

`ScriptResult` is renamed `ActionResult` in the same pass — it is now every action's
return type, and a macro returning a "ScriptResult" would be actively misleading.

### 4. Recording adds zero rows: the fourth button changes role

```
            ⭘  Name: … • Type: … • IP: …                     ← header

idle        [☰ Menu] [⌂ Home] [↩ Back] │ [ Macros ]

            ⭘  Name: … • Type: … • IP: …          ● RECORDING
recording
(append)    [☰ Menu] [⌂ Home] [↩ Back] │ [ ■ Stop ]

            ⭘  Name: … • Type: … • IP: …          ● RECORDING
recording
(capture 1) [☰ Menu] [⌂ Home] [↩ Back] │ [ ■ Cancel ]
```

The two modes read the same in the indicator and differ on the button: the indicator
reports state (a recording is running), the button is the thing you press.

The Stop control *is* the Macros button relabelled, and the divider before it is a
vertical `Rule` one row tall, offset down onto the buttons' middle line so it reads as a
mark between the two groups rather than a border spanning them.

*Why the divider:* Menu, Home, and Back send a key to the TV; Macros configures the
application. Without a break the fourth button reads as a fourth device key.

*Why relabelling rather than new rows:* the height budget above. A separate banner row
plus a Stop button row lands on the baseline with no slack, so any later addition to the
remote breaks the no-scroll test. Relabelling costs nothing vertically, and it reads
well: the button you pressed to start is the button you press to stop.

The indicator itself is a `Label` docked right inside `RemoteHeader`, a `Header`
subclass. It takes the slot of `HeaderClockSpace` — the ten-column spacer Textual
reserves for the optional clock, which this app never shows — hidden with
`display: none`, so the indicator sits flush right and `HeaderTitle` keeps those columns
while nothing is recording.

*Why the header:* it already carries application state (the connected device), so a
"recording" flag belongs beside it rather than among keys the user can press.

*Alternative rejected:* the header subtitle. `Screen.sub_title` works and is watched, but
`app.title` already holds `Name: … • Type: … • IP: …` at roughly 55 characters, so
appending a subtitle overflows 80 columns and truncates. A docked sibling widget avoids
that: it is laid out first and the title takes what is left.

*Trade-off accepted:* the indicator eats columns the title could use, and `HeaderTitle`
ellipsizes rather than wrapping. `● REC · ESC cancels` (nineteen columns) clipped the IP
address at 80 columns, so the indicator is the eleven-column `● RECORDING` and no longer
names the cancelling key. Escape-cancels stays discoverable from the `■ Stop` / `■ Cancel`
button and from Escape's back-a-page role everywhere else in the app.

*The indicator pulses.* Eleven static columns in a bar that always holds text read as
part of the device line; a slow fade out and back in is the one property no other part
of the header has, so the recording state is legible at a glance without a second row or
a wider indicator.

The fade animates `text_opacity` through a fixed ramp — `1.0, 0.85, 0.7, 0.55, 0.45` and
back — one stop every 120ms, so a cycle takes about a second.

*Why opacity, not color:* the user asked for a flashing indicator that stays red.
`text_opacity` blends the text toward the header's background, so every stop is a dimmer
red; cycling the `color` rule instead would take the indicator through hues that no
longer read as "recording". The floor is `0.45` rather than something nearer zero for the
same reason — below that the text blends into the header instead of dimming.

*Why a `set_interval` timer, not Textual's animation system:* `styles.animate` does not
repeat, so a pulse built on it has to chain a new leg from each leg's `on_complete` — an
animation that never completes. `App._press_keys` awaits `animator.wait_until_complete()`
after every key it sends, so `Pilot.press` would never return and every test that presses
a key while recording would hang. Stepping a ramp on a timer leaves the animator idle.
The cost is a stepped fade rather than a continuous one, which at five stops and a
terminal's color depth is not visible.

*Why the ramp resets on stop:* `stop_pulse` restores `text_opacity` to `1.0` before
hiding the label, so the indicator is never left dim — a capture-one recording that ends
and restarts (`+ Step`) begins its next pulse fully bright.

### 5. An in-memory draft carries edits across the round trip

Both Create Macro and Add Step leave a modal, land on the live remote, and come back.
The user may have renamed the macro and reordered its steps first.

```
              ┌─────────── draft: {name, steps[]} ───────────┐
              │        lives outside any one modal           │
              └─────────────────────────────────────────────┘
                   ▲                              │
   re-push w/ draft│                              │dismiss(draft)
                   │                              ▼
 ┌────────────┐  ┌─┴────────────┐  ┌──────────────────────────┐
 │ List Modal │─▶│ Detail Modal │─▶│ Remote (recording state) │
 └────────────┘  └──────────────┘  └──────────────────────────┘
       │                │                  ▲          │
       │ Create Macro   │ Save → prefs     │          │
       └────────────────┼──────────────────┘          │
                        └───────◀─────────────────────┘
```

The detail modal renders from the draft, never from the persisted macro. Save is the
only write to preferences. That is what makes Close-discards-changes true and Add Step
non-destructive.

Two record modes fall out:

| Mode | Entered from | Ends on | Returns to |
|---|---|---|---|
| `APPEND_UNTIL_STOP` | List → Create Macro | `■ Stop` | List, new macro selected |
| | | Escape | List, nothing saved |
| `CAPTURE_ONE` | Detail → Add Step | one captured action | Detail, draft + 1 step |
| | | Escape / `■ Cancel` | Detail, draft unchanged |

`CAPTURE_ONE` labels the fourth button `■ Cancel` rather than `■ Stop`: there is nothing
to stop, and pressing it returns without capturing — exactly what Escape does.

### 6. Modals are dismissed before recording, not layered under the remote

Because a modal freezes the screens below it (Decision 4's mechanism, in reverse), the
list and detail modals must be **dismissed** before recording starts — not hidden, not
left on the stack. The return path is a fresh push carrying the draft.

*Why this is worth stating:* "push the remote under the modal" or "hide the modal" both
look simpler and both produce a remote that ignores every key.

### 7. Step model

```
{"type": "key",      "key": "HOME"}
{"type": "text",     "text": "user@example.com"}
{"type": "action",   "action": {…frozen copy of a custom button's action…}}
{"type": "pause",    "ms": 1000}
```

A custom-button press is recorded as a **snapshot** — a frozen copy of the button's
resolved action dict — not a reference to the button index.

*Why:* the macro keeps working when the button is later reconfigured or when the same
macro runs on a device where that button index resolves to something different. A
reference would silently change what the macro does.

*Trade-off accepted:* retuning a custom button does not update macros that captured it.
That is the point, but it will occasionally surprise.

### 8. Nested macros are refused at record time, and again at playback

Because steps are snapshots, clicking a `run_macro` button while recording would freeze
`{"type": "run_macro", …}` into the step list — a step the detail modal would render as
`Run Macro: Login` and that could recurse forever:

```
Custom 3 ──action──▶ run_macro("login")
                          │
 macro "login".steps ─────┘──▶ [ …, snapshot of run_macro("login") ] ──▶ ∞
```

Record time refuses to capture it and says so. Playback keeps a depth guard that rejects
a `run_macro` reached from inside a macro — a rejected step is a failed step, so it aborts
the run per Decision 10, and hand-edited JSON cannot recurse either.

*Why refuse at record time rather than only at playback:* a playback-only guard lets the
user build a step that looks valid in the detail modal and always fails when run. Better
to say no immediately.

### 9. Playback owns its own modal, and never calls `present_result`

```
_activate_custom → _run_action → worker → run_macro(action, ctx)
                                              └─▶ await app.push_screen_wait(
                                                        MacroPlaybackModal(macro, ctx))
```

The modal's `on_mount` starts the step loop, each step updates its label
(`Step 3 of 12`), completion dismisses with a successful `ActionResult`, a failed step
dismisses with an unsuccessful one naming that step, and Cancel or Escape stops the loop
and dismisses. `run_macro` forwards whatever the modal returns, which is what makes the
aborted run read as a failure to the caller rather than as a partial success.

**The trap:** a snapshotted Run Custom Script action carries its `show_results` flag. The
per-step loop must call `run_action` directly and must **not** reuse
`RemoteScreen._execute`, which calls `present_result` — that would push a
`ScriptResultModal` on top of the playback modal, mid-macro, waiting on the user. Reusing
`_execute` looks like good reuse and is wrong.

`run_macro` therefore has no Results toggle in its config: the playback modal *is* the
progress UI, and a failing step already aborts with an error notification (Decision 10).

**The second trap, new with abort:** `_execute` calls `present_result(result,
show_results=action.get("show_results"))` on whatever `run_action` returns, and
`present_result` toasts `result.message` under the title **"Script failed"** whenever the
result is not ok. A macro used to return `ok=True` with a summary, so this never fired.
An aborted run returns `ok=False`, so it now fires — a second toast, mis-titled, after the
modal's own. The playback modal owns its reporting, so the catalog needs a way to say so:
`ActionType` gains `reports_own_outcome: bool = False`, set true for `run_macro`, and
`_execute` skips `present_result` for such a type. A cancelled run returns `ok=False` too
(it did not complete) and that flag is what keeps it silent, as the spec requires.

### 10. A failed step aborts the run

An unsupported key, a failed send, a non-zero script exit — each stops the macro where it
is. The modal dismisses, an error notification names the macro, the step, and the reason
(`Macro 'Login' failed at step 4 (Key: DOWN): device unreachable`), and the returned
`ActionResult` is unsuccessful. A completed run's message stays a summary
(`Macro 'Login': 12 steps`).

*Why:* a macro's later steps assume its earlier ones landed. `HOME, DOWN, DOWN, OK` with
one `DOWN` dropped does not do most of what the user asked — it opens the wrong thing.
Continuing past a failure converts a legible error into silent wrong behavior on the
device, which is worse than stopping. Aborting also keeps the notification unambiguous:
one error naming one step, not a stream of toasts the user has to reassemble.

*Consequence:* the cross-device capability gap is surfaced rather than absorbed. A macro
holding a digit step aborts on Apple TV at that step instead of skipping it. That is the
intended reading — the macro genuinely cannot do what it says on that device.

### 11. Default names use a monotonic counter, not a count

The registry persists `next_number` alongside its items. `Macro 1`, `Macro 2`, delete
`Macro 2`, next is `Macro 3`.

*Why:* `count + 1` collides after any deletion.

### 12. Macros persist inside the existing preferences file

```json
"macros": {
  "next_number": 4,
  "items": {
    "a3f9…": { "name": "Login", "steps": [ … ], "step_pause_ms": 500 }
  }
}
```

*Why:* macros are user configuration, exactly like `custom_buttons`, and reusing the
established path means the fault-tolerant load and best-effort save already apply.

*Alternative rejected:* a separate store file. `DeviceStore` is separate because devices
are a different domain with their own lifecycle; macros are not.

**The persistence chain has one link that silently eats data.** `App.persist_preferences`
rebuilds `Preferences` from explicit keyword arguments, and `watch_theme` calls it on
every theme change. Omitting `macros=` there means changing the theme wipes every macro
with no error. The chain must be completed end to end:

```
Preferences field → load() branch → save() key → app attr → on_mount() populate
                                                         → persist_preferences() kwarg
```

### 13. Deleting a macro is confirmed from inside the detail modal

Delete is destructive and unlike every other edit in the modal it is not covered by
Close-discards-changes (Decision 5) — the macro is gone from preferences. So it asks
first, reusing `ConfirmDeleteScreen` from `devices_screen.py`, which already reads
`Delete {name}?` and already focuses Cancel by default.

The prompt is pushed by the detail modal itself, and the modal dismisses with
`DELETE_MACRO` only once the user confirms — mirroring the device edit form, which
deletes and pops from inside its confirm callback.

*Alternative rejected:* dismiss with `DELETE_MACRO` first and have `RemoteScreen` confirm.
The draft would already be gone from the screen stack, so Cancel would have to re-push the
detail modal to restore it — a visible flicker and a second place holding the draft, to
buy nothing.

### 14. One editable default gap per macro, 500 ms, additive with pause steps

Every macro carries `step_pause_ms` (default 500) and playback sleeps it before each step
after the first:

```
step 1 ──▶ gap ──▶ step 2 ──▶ gap ──▶ [pause 2000] ──▶ gap ──▶ step 3
           500              500          2000          500
```

*Why per-macro rather than one global preference:* the right gap is a property of what the
macro drives — a TV app that redraws slowly needs a longer one than a settings menu — and
a global value would be tuned for the slowest macro and waste time in every other. It also
keeps the value where the user is already editing that macro.

*Why 500 ms:* keys sent back to back land faster than most TV UIs redraw, so the naive
macro recorded before this existed replayed too fast to work. Half a second is slow enough
for a typical menu transition and short enough that a ten-step macro still finishes in
seconds.

*Why additive rather than a floor:* a pause step means "wait longer here", and reading it
as a replacement would make a 100 ms pause step *shorter* than no pause step at all.

*Why not before the first step or after the last:* the gap exists to separate one send from
the next. A leading gap only delays the whole run, and a trailing one delays the modal's
dismissal for nothing.

The sleep happens **before** `self._index` advances, so a cancel landing inside a gap
reports the last step that actually ran rather than one that never started.

The input costs the detail modal three rows (a `Label` beside a bordered `Input`), which
80×24 does not have spare: the fixed rows already leave the `1fr` step list three rows.
The three vertical margins inside the modal — under the title, under the name input, and
above the button row — pay for it, so the list keeps the same height it had.

## Risks / Trade-offs

- **`persist_preferences` omission wipes every macro.** → Decision 12 names it; a test
  asserts macros survive a theme change (mirroring the existing "actions coexist with
  theme, shortcuts, and titles" scenario).
- **Reusing `_execute` for playback steps pops a result modal mid-macro.** → Decision 9
  names it; a test plays a macro containing a snapshotted script step with
  `show_results: true` and asserts no result modal appears.
- **Recording UI pushes the remote past the no-scroll baseline.** → Decision 4 makes
  recording cost zero rows, so the existing test stays green by construction rather than
  by measurement.
- **A recording that leaves a modal on the stack produces a dead remote.** → Decision 6;
  a test records a key press and asserts the step was captured.
- **Cancel during a script step leaves a lingering `/bin/sh`.** `run_script`'s 30-second
  timeout means three script steps can run 90 seconds; cancelling the worker cancels the
  `await`, but the spawned shell may outlive it. → Accepted. The script is the user's own
  on their own machine, and the existing timeout still reaps it.
- **A macro recorded on one device aborts partway on another.** A key the target adapter
  lacks stops the run at that step instead of skipping it, so a macro can leave the device
  half-navigated with nothing undone. → Accepted (Decision 10). Stopping at a legible
  failure beats sending the remaining steps into whatever state the device is actually in.
  The error names the step, so the user can see which key the device does not support.
- **A snapshotted step goes stale when its custom button is retuned.** → Accepted and
  intended (Decision 7). The detail modal renders the snapshot's own description so what
  is shown is what will run.
- **A button pointing at a deleted macro.** → Playback reports it and does nothing
  (Decision 2). Deleting a macro does not walk the custom-button map to clean up
  references.
- **The Macros hint cannot fit in the footer.** → The button is mouse-reachable and the
  action is registered with `show=False`, matching how Go Back is already handled.
- **The default-pause input collapses the step list at 80×24.** A `1fr` list starved to
  zero rows renders blank while every assertion about the buttons still passes. →
  Decision 14 pays for the row with the modal's three vertical margins, and the existing
  short-terminal test is the check.

## Migration Plan

No data migration. `Preferences.load` already tolerates a missing key, so an existing
`settings.json` loads with an empty macro registry. The renames (`ScriptResult` →
`ActionResult`) and the widened runner are internal; no persisted data references
either.

Rollback is a revert: a `settings.json` written by this change carries an extra `macros`
key that an older build ignores on load — but note that an older build's `save` would
then drop it, so a downgrade after creating macros loses them.

## Open Questions

None blocking. Deferred by choice:

- Additional invocation surfaces (a Play button in the list modal, a dedicated hotkey,
  a CLI trigger). The stable macro id is what makes these cheap to add later.
- Recording the real wall-clock gaps between presses as implicit pauses.
- Cleaning up custom buttons that reference a macro when it is deleted.
