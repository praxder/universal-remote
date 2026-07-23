## 1. Persistence: layered custom-button titles

- [x] 1.1 Write failing tests for `PreferencesStore` round-tripping a `custom_buttons` map: saving/loading it, defaulting to empty when the key is absent (back-compat), and not disturbing `theme` or `shortcuts`
- [x] 1.2 Extend the `Preferences` dataclass with `custom_buttons: dict` (default empty) and update `PreferencesStore.load`/`save` to read/write it with the existing fault-tolerant behavior
- [x] 1.3 Write failing tests for a title resolver: device → type → global → `Custom N` precedence, blank/absent entries falling through, and the default when no scope matches
- [x] 1.4 Add the custom-button resolver module (title resolution by scope), keeping resolution separate from the raw store

## 2. Text entry via a modal

- [x] 2.1 Write failing tests for a `TextEntryModal`: typing + Enter sends the buffered text once and dismisses; Escape dismisses without sending text or Back; unsupported-text surfaces a message and opens no editable input
- [x] 2.2 Implement `TextEntryModal`, moving the `send_text` path (including the ADB-fallback status message) into it
- [x] 2.3 Remove the docked `TextField` and `#text-status` label from `RemoteScreen.compose`; make `action_text_mode` push the modal, and surface the unsupported-text message (toast) instead of the removed label
- [x] 2.4 Update/replace existing remote-screen tests that queried `#text` / `#text-status`

## 3. Custom button row on the remote

- [x] 3.1 Write failing tests: the remote renders five custom buttons reading `Custom 1`–`Custom 5` by default, and shows resolved titles when the app has saved custom-button data for the active device
- [x] 3.2 Add the `#custom-row` of five buttons to `RemoteScreen.compose`, styled with the existing `#remote Button` CSS
- [x] 3.3 Resolve and label each custom button on mount from the app's `custom_buttons` map and the active device

## 4. Button configuration modal

- [x] 4.1 Write failing tests for `ButtonConfigModal`: title input, three-way scope selector defaulting to This Device, disabled Action Type placeholder, OK saves the title at the selected scope and Cancel discards
- [x] 4.2 Implement `ButtonConfigModal` (title + scope + disabled Action Type placeholder + OK/Cancel)
- [x] 4.3 On OK, write the title into the selected scope's slot for that button, persist via the store, and re-resolve the button's label; on Cancel, dismiss with no change
- [x] 4.4 Write failing test that clicking a custom button opens its config modal (inert: click always opens config in this phase)
- [x] 4.5 Wire the custom-button click to open `ButtonConfigModal` for that button
- [x] 4.6 In `app.py`, load/save the `custom_buttons` map and expose the resolver to screens, mirroring `shortcut_overrides`

## 5. Docs, spec sync, and preflight

- [x] 5.1 Update in-repo docs/README (and any screenshots) that describe the "press T to type" bar to reflect the custom-button row and text modal
- [x] 5.2 Run the formatter and linter; fix all warnings
- [x] 5.3 Run the full test suite (including the short-terminal `does_not_scroll` baseline) and fix any failures

## 6. Refinements (this revision)

### 6.1 Keyboard shortcuts for the custom buttons
- [ ] 6.1.1 Write failing tests: the catalog exposes five rebindable Remote actions `remote.custom_1`–`remote.custom_5` with empty default keys; the Keyboard Shortcuts table lists them under Remote; assigning one and pressing it on the remote activates the matching button (same effect as a click)
- [ ] 6.1.2 Add the five `remote.custom_N` actions to `CATALOG` in `tui/shortcuts.py` (Remote scope, empty default key, `show=False`), targeting `activate_custom(N)`
- [ ] 6.1.3 Route the custom-button click and the shortcut through a single `_activate_custom(index)` method — both `on_button_pressed`'s `custom-` branch and a new `action_activate_custom` call it — so Phase 2 can upgrade activation (run-or-config) in one place (Phase 1: it opens the config modal)

### 6.2 Saved title resizes the button immediately
- [ ] 6.2.1 Write a failing test: after saving a longer/shorter title, the custom button's rendered width reflects the new title without re-mounting the remote
- [ ] 6.2.2 Force a layout refresh after relabeling in `RemoteScreen._label_custom` (the `label` reactive is `layout=False`, so text repaints but the auto-width stays stale)

### 6.3 Static config-modal heading
- [ ] 6.3.1 Write a failing test: the Button Config modal heading reads the fixed "Configure Custom Button" for every button
- [ ] 6.3.2 Change the `ButtonConfigModal` heading label to the static text "Configure Custom Button"

### 6.4 Scope selector reflects the stored scope
- [ ] 6.4.1 Write failing tests for a scope resolver: it returns the scope of the first non-blank title in device→type→global order (reusing `resolve_title`'s order), and None when no title is configured
- [ ] 6.4.2 Add the scope resolver to `tui/custom_buttons.py`
- [ ] 6.4.3 Write a failing test: reopening a button saved at Global preselects Global (not This Device); an unconfigured button still defaults to This Device
- [ ] 6.4.4 Preselect the resolved scope's radio in `ButtonConfigModal.compose`, defaulting to This Device when the resolver returns None

### 6.5 Deleting a device purges its device-scoped custom buttons
- [ ] 6.5.1 Write failing tests: deleting a device removes that device's device-scoped `custom_buttons` entries while leaving device-type and global entries intact, and persists the change
- [ ] 6.5.2 Add a device-purge helper to `tui/custom_buttons.py` (remove the device-scope slot for a device id)
- [ ] 6.5.3 Coordinate the device-store delete and the custom-button purge in one place — prefer an app-level `delete_device(id)` that deletes from the store, purges the device-scoped entries, and persists — called from both device-delete sites in `tui/devices_screen.py` (the list `action_delete` and the edit-screen `_delete`) rather than duplicating the two-store logic at each site

### 6.6 Cross-change sync and preflight
- [ ] 6.6.1 Keep Phase 2 (`add-custom-button-actions`) in sync: its `tui-remote` MODIFIED blocks for "Custom buttons on the remote" and "Custom button configuration modal" carry the scope-preselect, immediate-resize, static-heading, and keyboard-activation wording so archiving Phase 1 then Phase 2 does not revert them; Phase 2's run-or-config upgrade MUST go through the shared `_activate_custom(index)` from 6.1.3 so the shortcut and click stay identical (else the Phase 2 keyboard-activation scenario silently fails)
- [ ] 6.6.2 Update in-repo docs/README (shortcuts screen and custom-button sections) for the five new shortcuts
- [ ] 6.6.3 Run the formatter and linter; fix all warnings
- [ ] 6.6.4 Run the full test suite and fix any failures
