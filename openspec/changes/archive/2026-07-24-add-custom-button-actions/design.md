## Context

Phase 1 (`add-custom-remote-buttons`) delivers the five-button custom row, the Button Config modal (title + three-way scope, with a *disabled* Action Type placeholder), and the layered `custom_buttons` persistence keyed by device / device-type / global. Each stored entry is already an object (`{ "title": ... }`) specifically so Phase 2 can add an `"action"` field without a schema migration.

Phase 2 attaches behavior to those buttons: an extensible action catalog whose first (and, for now, only) action is Run Custom Script. This is the app's first feature that executes arbitrary user-provided shell, so the execution seam and its trust boundary are the load-bearing parts.

**This change stacks on Phase 1, which is now archived.** Its `tui-remote` deltas MODIFY requirements Phase 1 introduced; those are live now, so Phase 2 is ready to apply.

## Goals / Non-Goals

**Goals:**
- Assign an action to a custom button, persisted at the same three scopes as the Phase-1 title and resolved jointly with it — the entry resolves as a unit, most-specific-first.
- Ship one action, Run Custom Script, behind a catalog that accepts more action types later without reworking the surface or the config modals.
- Run a configured button's action on click without freezing the TUI; leave inert (no-action) buttons opening config.
- Let the user choose whether a run surfaces its output (a result modal) or stays quiet unless it fails (an error toast).
- Inject the connected device's IP as `REMOTE_IP` into the script environment.

**Non-Goals:**
- Any action type beyond Run Custom Script (the catalog is built to extend; the entries are not).
- Sandboxing, permission prompts, or vetting of script contents (see trust model).
- Cross-device action sync or import/export.
- Revisiting Phase-1 decisions (the scope-selector widget, the text-entry modal) — those are settled in the archived Phase 1.

## Decisions

### Decision: An extensible action catalog, one action for now
Actions are modeled as a small typed catalog (each action type has an id, a display label, a config modal, and a runner), mirroring how `shortcuts.py` centralizes a catalog. Phase 2 registers exactly one: `run_script` → "Run Custom Script". The Action Type list modal renders the catalog; adding a future action type means adding a catalog entry plus its config modal and runner, not touching the button surface.
- **Why**: The user explicitly wants this list to grow ("these actions will be extensible in the future"). A catalog keeps the surface stable.

### Decision: Run-on-click iff an action is set; edit gesture opens config
A custom button with a resolved action RUNS it on click. A button with no action opens the Button Config modal (unchanged from Phase 1). To re-edit a button that has an action, the user uses a distinct **edit gesture** rather than a plain click.
- **Edit gesture**: an explicit *edit-mode key* on the remote — press it to arm edit-mode, then activate a custom button (click it, or press its shortcut) to open that button's config; the mode clears after one activation. This is the guaranteed path because a modifier-click cannot carry the intent reliably: Cmd+Click is structurally undetectable (the xterm mouse protocol has no Command-key bit and Textual exposes only `shift`/`meta`(=Alt/Option)/`ctrl` on a click), and Alt/Option- or Shift+Click are commonly hijacked by macOS terminals for text selection. The edit-mode key needs no mouse-modifier support and works on every terminal. **Resolve the exact keycap during implementation** against the existing remote key map (must not collide with a reserved D-pad/Vim key); the mechanism (arm → next activation configures → clear) is settled.
- **Keyboard interaction with Phase-1 shortcuts**: Phase 1 already added five rebindable "Activate Custom Button 1–5" shortcuts that mirror a click. In Phase 2 that mirror means they RUN a configured button's action (and open config for an inert one) — so those shortcuts are the keyboard *run* path. Arming edit-mode flips the next activation to the *configure* path, and it flips click and shortcut alike, so a shortcut still behaves identically to a click (both run when edit-mode is off, both configure when it is armed). All of it flows through the shared `_activate_custom` / config dispatch, so activation stays identical whether it came from a click or a shortcut.
- **Why**: A physical-remote feel means click = fire. The Phase-1 rule "click runs iff the button has a runnable action" was written to switch on here.
- **Edit-mode key = `e`, and it toggles** (second-pass refinement): the resolved keycap is `e`, reserved so it can't be reassigned. Pressing `e` while edit-mode is armed disarms it (no config opens), so `e` is a toggle rather than a one-way arm — the user who armed it by mistake gets out with the same key. `e` is shown in the remote footer as the short **"Edit"** hint (its full "Configure Custom Button" label stays in the Keyboard Shortcuts table). The footer holds ~8 hints within the supported 80-column width; to fit "Edit" without clipping, the four D-pad arrow hints are dropped from the footer — the on-screen ▲▼◀▶ glyphs already label those directions, and the table still lists them. The short footer text comes from a new `footer_label` field on the catalog `Action` so a long table label and a short footer hint can differ.
- **Re-editing prefills the action** (second-pass refinement): reopening a configured button's Action Type → Run Custom Script config prefills the stored source, script/path, and Results choice instead of a blank form. The Button Config modal threads the button's current action into the Action Type list, which forwards it to a chosen type's config modal only when the type matches — so prefill stays correct as the catalog grows.

### Decision: Run Script config modal — source toggle, results toggle, REMOTE_IP helpline
`RunScriptConfigModal` contains:
- **Source toggle**: Script File / Inline Script.
  - File → a one-line path input to a shell script.
  - Inline → a multi-line editor (Textual `TextArea`) for shell script text.
- **Results toggle**: Don't Show / Show (see execution decision for semantics).
- A **helpline**: `REMOTE_IP` is set in the environment to the connected device's IP address when the script runs.
- OK / Cancel.

Reached by: custom-button click (no action) → Button Config modal → Action Type control → Action Type list → Run Custom Script → this modal. OK stores the script config into the button's action for the scope chosen in the Button Config modal.
- **Why**: This is the modal the user described, plus the Results toggle decided in exploration.

### Decision: Non-blocking execution model with an explicit trust boundary
Scripts run in a Textual worker via an asyncio subprocess so the event loop never blocks. Concrete choices:
- **Invocation**: inline scripts run as `/bin/sh -c <script>`; file scripts execute the given path. `/bin/sh` is used unconditionally for inline scripts — no shebang parsing and no `$SHELL` honoring.
- **Environment**: the process environment plus `REMOTE_IP=<device.ip>` — the connected device's IP, available on the remote screen as `self._device.ip`. This is the only injected value.
- **Timeout**: a fixed 30-second timeout kills a hung script; on timeout the run is treated as a failure. The value is not user-configurable in this phase (a later change can add per-action configuration if it proves necessary).
- **Results visibility** (from the Results toggle):
  - **Don't Show** → success is silent (no UI); a non-zero exit (or timeout/spawn failure) raises an **error toast** naming the failure.
  - **Show** → a result modal reports success or failure with the script's exit code and its full output (stdout/stderr), shown in a scrollable modal so long output is never truncated.
- **Why**: TUI responsiveness is non-negotiable; the user chose the quiet-unless-error vs. always-show split.

### Decision: Trust model — user's own shell on the user's own machine
The feature runs arbitrary shell the same user authored, on their own machine, under their own privileges. There is **no sandbox and no content vetting**; `REMOTE_IP` is the only value the app injects; the timeout is a reliability guard, not a security control. This trust boundary is stated so it is a deliberate, documented choice rather than an oversight.
- **Why**: The advisor flagged that arbitrary-shell execution must name its trust model explicitly. It is legitimate for personal automation but should never be silent.

### Decision: Persist the action in the existing entry, resolved jointly with the title
The Phase-1 custom-button entry gains an optional `"action"` object, e.g.:
```json
"custom_buttons": {
  "device": { "<device.id>": { "1": {
    "title": "Reboot",
    "action": { "type": "run_script", "source": "inline",
                "script": "...", "show_results": false }
  } } }
}
```
The action resolves from the same scope as the title: the entry resolves as a single unit, most-specific-first (device → type → global), so a button's title and action always come from the same stored entry and are never split across scopes. The scope chosen in the Button Config modal governs both.
- **Why**: Reuses the Phase-1 store, resolver, and precedence; no migration. A single scope choice in the modal governs the whole button, matching the user's mental model.
- **Alternative considered**: resolving the title and action independently, each from its own most-specific scope — rejected; it would let a button mix a title from one scope with an action from another, splitting one scope choice in two and surprising the user.

## Risks / Trade-offs

- **Arbitrary code execution** → by design; mitigated only by being the user's own scripts on their own machine and by documenting the trust boundary. The timeout bounds runaway/hung scripts but is not a security boundary.
- **Hung or long-running script** → the bounded timeout kills it and reports failure; the worker keeps the UI responsive meanwhile.
- **Archiving Phase 2 later** → the `tui-remote` MODIFIED requirements change two scenarios Phase 1 put in the live specs — "Clicking a custom button opens its configuration" (narrowed to the no-action case, plus a new run-it scenario) and "Action Type is a disabled placeholder" (flips to active). The archive drop-guard will flag both. Keep the header and edit in place for the first; the second is a genuine flip with no in-place edit, so it is an archive-time decision (see tasks). This is not a blocker for applying Phase 2.
- **`TextArea` availability/behavior** → confirm Textual's `TextArea` fits the inline-script editor (multi-line, focus, Escape handling within a modal) during implementation.
- **File-source path validation** → a missing/non-executable path should fail like a non-zero exit (error toast or result modal), not crash the remote — handle in the runner.

## Migration Plan

No data migration. Phase-1 entries without an `"action"` field load as title-only, inert buttons (click opens config). Adding an action is a normal save. Rollback removes Phase 2 behavior; a leftover `"action"` field is simply ignored by the Phase-1 loader.

## Open Questions

All resolved during scoping: inline scripts run under `/bin/sh -c` (no shebang/`$SHELL` honoring); the execution timeout is a fixed, non-configurable 30 seconds; the Show result modal presents full, untruncated output in a scrollable view; and the edit gesture is an edit-mode key followed by a custom-button activation (Cmd+Click having been ruled out as structurally undetectable in a terminal). The only detail deferred to implementation is the exact edit-mode keycap, chosen against the reserved remote key map.
