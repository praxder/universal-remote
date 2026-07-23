## Why

Phase 1 (`add-custom-remote-buttons`) put five relabel-able custom buttons on the remote and the layered per-scope persistence behind them — but the buttons are inert. Phase 2 makes them do something: it adds an extensible action catalog and its first action, Run Custom Script, so a user can attach a shell script (file or inline) to a button and fire it from the remote. This is the payoff the Phase-1 surface was built for.

**Depends on `add-custom-remote-buttons` (Phase 1).** Phase 2 assumes Phase 1's custom-button row, config modal, and `custom_buttons` persistence are implemented and its spec deltas archived into the live specs. Implement and archive Phase 1 first.

## What Changes

- **Add an extensible action catalog.** A custom button MAY be assigned an action. The catalog starts with a single action, **Run Custom Script**, and is structured so more action types can be added later without reworking the surface.
- **Activate the Action Type control** in the Button Config modal (a disabled placeholder in Phase 1). Selecting it opens an Action Type list modal; in this phase the list holds one entry, Run Custom Script.
- **Add the Run Script config modal.** It offers a source toggle (Script File / Inline Script): file shows a one-line path input to a shell script; inline shows a multi-line editor for a shell script. A helpline states that `REMOTE_IP` is set in the script's environment to the connected device's IP. A Results toggle (Don't Show / Show) selects how output surfaces. OK / Cancel.
- **Run a configured button on click.** A custom button that has an action RUNS it on click; a button with no action still opens config (the Phase-1 rule "click runs iff the button has an action" now has its left branch). Re-editing a configured-with-action button uses a distinct edit gesture (edit-mode key or modifier-click — see design).
- **Execute scripts without blocking the UI.** Scripts run in a background worker via an async subprocess, with `REMOTE_IP` in the environment, a bounded timeout that kills a hung script, and results surfaced per the Results toggle: Don't Show → silent on success, an error toast on a non-zero exit; Show → a result modal with success/failure and output.
- **Persist the action** alongside the Phase-1 title in each custom-button entry (the entry is already an object for this reason), keyed by the same device / device-type / global scopes.

## Capabilities

### New Capabilities
- `custom-button-actions`: The action catalog assignable to a custom button, its first action Run Custom Script (file or inline source), the non-blocking script-execution model (`REMOTE_IP` injection, timeout, exit-code handling), the Results-visibility modes, and the trust model for running user shell scripts.

### Modified Capabilities
- `tui-remote`: The custom-button click now runs an assigned action (or opens config when none); the Action Type control becomes active and opens the Action Type list; the Run Script config modal is added; a configured-with-action button gains an edit gesture. (Modifies requirements introduced by Phase 1.)
- `app-preferences`: Each custom-button entry additionally persists its assigned action, at the same three scopes as the title, resolved most-specific-first. (Adds to the Phase-1 persistence.)

## Impact

- **Code**: New action-execution module (async worker + subprocess, `REMOTE_IP` env, timeout, exit-code/output capture). New `ActionTypeListModal` and `RunScriptConfigModal`. `tui/remote_screen.py` (custom-button click dispatches run-or-config; edit gesture opens config; label/state reflect whether an action is set). Button Config modal (Action Type control activated, wired to the list modal). Persistence: extend the custom-button entry with an `action` blob and its resolver. `tui/app.py` (thread the active device's IP to the executor).
- **Security / trust model**: Running arbitrary user shell on the user's own machine is the point of the feature; scripts are authored by the same user operating the app. The design MUST state this trust boundary explicitly (no sandboxing; `REMOTE_IP` is the only injected value; the bounded timeout is a safety net, not a security control).
- **No new runtime dependencies expected** (async subprocess via the standard library).
