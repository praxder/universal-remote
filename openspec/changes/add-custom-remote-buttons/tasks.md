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
