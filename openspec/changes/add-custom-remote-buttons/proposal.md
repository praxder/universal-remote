## Why

The remote's bottom edge is a single always-present text field with a status label — a lot of vertical space spent on a rarely-used control, and no room for the user to add their own controls. Users want a small set of personal buttons on the remote they can name and, later, wire to actions. This change (Phase 1 of two) reclaims that space: it moves text entry into an on-demand modal and puts five relabel-able, per-scope-persisted custom buttons in its place. Phase 2 will make those buttons run actions; Phase 1 delivers the surface and the persistence it needs.

## What Changes

- **Remove** the always-visible inline text field and its status label from the bottom of the remote surface.
- **Move text entry into a modal.** The Text action (default `t`) now opens a modal with a text input; submitting sends the buffered text and closing it returns to the remote. The compose-then-send and Escape-exits behavior is unchanged — only its presentation moves from a docked field to a pop-up.
- **Add a row of five custom buttons** at the bottom of the remote, styled like the existing remote buttons. They default to the titles `Custom 1` through `Custom 5`.
- **Clicking a custom button opens a Button Config modal** with: a Button Title text input, a three-way scope toggle (This Device / Device Type / Global), a disabled "Action Type" control shown as a Phase-2 placeholder, and OK / Cancel. Saving relabels the button; Cancel discards.
- **Custom buttons are inert in Phase 1** — they carry a title and a scope but no action, so a click always opens the config modal (there is nothing to run yet). The run-on-click and edit-gesture behavior arrives in Phase 2.
- **Persist button titles per scope** in `settings.json` under a new layered `custom_buttons` structure, keyed by scope (specific device id, device-type/platform, or global). A button's shown title resolves most-specific-first: this device, then device type, then global, then the `Custom N` default.

### Refinements to the shipped surface (this revision)

Follow-up corrections and one small addition to the surface above, folded in before archive:

- **Keyboard shortcuts for the custom buttons.** Add five rebindable Remote actions — Activate Custom Button 1 through 5 — to the shortcut catalog, each defaulting to no shortcut. Activating one behaves exactly like clicking that button (so in this phase it opens the button's config modal; it upgrades to running the action in Phase 2). Hidden from the footer to preserve its eight-hint fit.
- **Relabel resizes the button immediately.** Saving a longer or shorter title updates the button's width right away instead of only after the remote is reopened. (Setting the Button `label` reactive repaints text but does not invalidate layout, so the auto-width was stale; the fix forces a layout refresh after relabeling.)
- **Static config-modal heading.** The Button Config modal's heading is the fixed text "Configure Custom Button" rather than "Configure Custom N".
- **Scope selector reflects the stored scope.** On open, the scope selector preselects the scope the shown title resolves from (device → type → global), defaulting to This Device only when no title is configured at any scope — so reopening a button edited to Global shows Global, not This Device.
- **Deleting a device purges its device-scoped custom buttons.** Removing a saved device also removes that device's device-scoped `custom_buttons` entries, leaving device-type and global entries intact.

## Capabilities

### New Capabilities
<!-- None. The action/execution engine is deferred to Phase 2 and will introduce a new capability then. -->

### Modified Capabilities
- `tui-remote`: The on-screen remote surface replaces the docked text field with a five-button custom row; text entry becomes a modal; a new Button Config modal names and scopes a custom button (static heading; scope selector reflects the stored scope; a saved title resizes the button immediately); a custom button can also be activated by an assigned keyboard shortcut.
- `app-preferences`: Preferences gain a layered `custom_buttons` store (title per button per scope) persisted alongside the theme and shortcuts, with the same fault-tolerant read/write behavior; deleting a device purges that device's device-scoped entries.
- `keyboard-shortcuts`: The rebindable action catalog gains five Remote-surface custom-button activation actions (Activate Custom Button 1–5), each defaulting to no shortcut and mirroring a click of the matching button.

## Impact

- **Code**: `tui/remote_screen.py` (drop the inline `TextField` + `#text-status`; add the custom-button row; resolve and label the buttons on mount; the Text action pushes a modal). New text-entry modal and Button Config modal (new `ModalScreen`s, following existing modal patterns). New custom-button resolver module (title resolution by scope), mirroring how `shortcuts.py` holds resolution logic separate from the raw store. `tui/app.py` (load/save the new `custom_buttons` map and expose the resolver to screens, mirroring `shortcut_overrides`). `preferences/store.py` (extend `Preferences` + JSON read/write with `custom_buttons`, defaulting to empty for back-compat).
- **Refinements**: `tui/shortcuts.py` (five `remote.custom_N` catalog actions, empty default key, `show=False`) and `tui/remote_screen.py` (an `action_activate_custom` that reuses the click dispatch; a layout refresh after relabel; the static modal heading; scope preselect from a resolver that reuses the title-resolution order). `tui/custom_buttons.py` (a scope resolver mirroring `resolve_title`, and a device-purge helper). An app-level `delete_device(id)` that coordinates the device-store delete and the custom-button purge in one place, called from both delete sites in `tui/devices_screen.py` instead of duplicating the two-store logic.
- **Persistence**: New `custom_buttons` key in `settings.json`; existing files without it load cleanly with an empty map.
- **No new dependencies.** No behavior change to key sending, capabilities, or device connections.
