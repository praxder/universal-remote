## Why

The remote's bottom edge is a single always-present text field with a status label — a lot of vertical space spent on a rarely-used control, and no room for the user to add their own controls. Users want a small set of personal buttons on the remote they can name and, later, wire to actions. This change (Phase 1 of two) reclaims that space: it moves text entry into an on-demand modal and puts five relabel-able, per-scope-persisted custom buttons in its place. Phase 2 will make those buttons run actions; Phase 1 delivers the surface and the persistence it needs.

## What Changes

- **Remove** the always-visible inline text field and its status label from the bottom of the remote surface.
- **Move text entry into a modal.** The Text action (default `t`) now opens a modal with a text input; submitting sends the buffered text and closing it returns to the remote. The compose-then-send and Escape-exits behavior is unchanged — only its presentation moves from a docked field to a pop-up.
- **Add a row of five custom buttons** at the bottom of the remote, styled like the existing remote buttons. They default to the titles `Custom 1` through `Custom 5`.
- **Clicking a custom button opens a Button Config modal** with: a Button Title text input, a three-way scope toggle (This Device / Device Type / Global), a disabled "Action Type" control shown as a Phase-2 placeholder, and OK / Cancel. Saving relabels the button; Cancel discards.
- **Custom buttons are inert in Phase 1** — they carry a title and a scope but no action, so a click always opens the config modal (there is nothing to run yet). The run-on-click and edit-gesture behavior arrives in Phase 2.
- **Persist button titles per scope** in `settings.json` under a new layered `custom_buttons` structure, keyed by scope (specific device id, device-type/platform, or global). A button's shown title resolves most-specific-first: this device, then device type, then global, then the `Custom N` default.

## Capabilities

### New Capabilities
<!-- None. The action/execution engine is deferred to Phase 2 and will introduce a new capability then. -->

### Modified Capabilities
- `tui-remote`: The on-screen remote surface replaces the docked text field with a five-button custom row; text entry becomes a modal; a new Button Config modal names and scopes a custom button.
- `app-preferences`: Preferences gain a layered `custom_buttons` store (title per button per scope) persisted alongside the theme and shortcuts, with the same fault-tolerant read/write behavior.

## Impact

- **Code**: `tui/remote_screen.py` (drop the inline `TextField` + `#text-status`; add the custom-button row; resolve and label the buttons on mount; the Text action pushes a modal). New text-entry modal and Button Config modal (new `ModalScreen`s, following existing modal patterns). New custom-button resolver module (title resolution by scope), mirroring how `shortcuts.py` holds resolution logic separate from the raw store. `tui/app.py` (load/save the new `custom_buttons` map and expose the resolver to screens, mirroring `shortcut_overrides`). `preferences/store.py` (extend `Preferences` + JSON read/write with `custom_buttons`, defaulting to empty for back-compat).
- **Persistence**: New `custom_buttons` key in `settings.json`; existing files without it load cleanly with an empty map.
- **No new dependencies.** No behavior change to key sending, capabilities, or device connections.
