## Context

The remote surface (`tui/remote_screen.py`) ends in an always-visible `TextField` (disabled until the Text action fires) plus a `#text-status` label. That fixed footer costs vertical space and offers no user-extensible controls. This change is Phase 1 of a two-phase effort to add per-user custom buttons: Phase 1 builds the surface, the config modal, and the layered persistence; Phase 2 adds the action catalog and the script-execution engine.

Two existing patterns are load-bearing here:
- **Modals** are routine (`CaptureModal`, `ConfirmDeleteScreen`, the connect/pair modals). The text-entry and Button Config modals follow the same `ModalScreen[...]` shape.
- **Preferences** already persist per-action data in `settings.json` via `PreferencesStore`, with a frozen `Preferences` dataclass and fault-tolerant read/write. Custom-button data slots into the same file.

The `Scope` enum in `shortcuts.py` (HOME/GLOBAL/REMOTE) is unrelated — it scopes *keyboard actions* to screens. Custom-button scope is a new, orthogonal concept (device / device-type / global) and gets its own type.

## Goals / Non-Goals

**Goals:**
- Replace the docked text field with an on-demand text-entry modal; preserve compose-then-send and Escape-exits behavior exactly.
- Show five custom buttons on the remote, styled like the existing buttons, defaulting to `Custom 1`–`Custom 5`.
- Let a click open a Button Config modal that sets a per-scope title.
- Persist titles in `settings.json` under a layered `custom_buttons` map and resolve the shown title most-specific-first (device → type → global → default).
- Keep existing `settings.json` files loading cleanly (empty custom-button map when the key is absent).

**Non-Goals (Phase 2):**
- Any action a button runs. Phase 1 buttons are inert.
- The Action Type list modal, the Run Script config modal, and the "Show results" toggle.
- The script-execution engine (workers, subprocess, `REMOTE_IP`, timeouts, output surfacing).
- The run-on-click behavior and the edit gesture (edit-mode key / modifier-click) for a *configured-with-action* button.

## Decisions

### Decision: Text entry moves to a modal, keeping identical send semantics
The Text action (`action_text_mode`) pushes a new `TextEntryModal` instead of enabling a docked field. The modal owns the `Input`; on submit it calls the same `session.send_text(...)` path (including the existing ADB-fallback status message), then dismisses. Escape dismisses without sending. The `#text` field and `#text-status` label are removed from `compose`; the status messages they carried (unsupported text, send failure, ADB fallback) move into the modal or a toast.
- **Why**: The user asked for text to remain reachable but stop occupying the footer. A modal is the established pattern and frees the row for the custom buttons.
- **Alternative considered**: Keep the field but collapse it when idle — rejected; still reserves layout and complicates focus handling.

### Decision: Five custom buttons in their own centered row, reusing the remote button style
A new `#custom-row` `Horizontal` yields five `Button`s with ids like `#custom-1`. They inherit the `#remote Button` CSS (bordered, height 3), matching the other groups.
- **Why**: "Match the style of the other buttons on this page." Five is the fixed count the user specified.

### Decision: Extend `PreferencesStore`; put resolution in a separate module
`Preferences` gains `custom_buttons: dict` (default empty). `PreferencesStore.load/save` read/write it with the same fault tolerance as `shortcuts`. Title resolution lives in a new small module (e.g. `custom_buttons.py`), not in the store — mirroring how `shortcuts.py` holds resolution while `PreferencesStore` holds only the raw dict.
- **Why**: One config file, one XDG path, one fault-tolerance policy already exist — a second store would duplicate all three. Keeping the store dumb and resolution separate matches the shortcuts split and keeps the JSON shape stable for Phase 2.
- **Alternative considered**: A dedicated `CustomButtonsStore` — rejected as premature duplication.

### Decision: JSON shape is scope-keyed, indexed by button
```json
"custom_buttons": {
  "device": { "<device.id>": { "1": { "title": "Netflix" } } },
  "type":   { "<platform>":  { "1": { "title": "Kids" } } },
  "global": {                  "1": { "title": "Reboot" } }
}
```
Each entry is an object (not a bare string) so Phase 2 can add `"action": {...}` without a schema migration. Button index is 1-based to match the visible `Custom N` labels.
- **Why**: Nesting by scope keeps the three scopes independent and makes resolution a three-key lookup. Object-valued entries are forward-compatible.

### Decision: Title resolution is most-specific-first
For button `i` on device `d` (platform `p`): `device[d.id][i]` → `type[p][i]` → `global[i]` → `"Custom {i}"`. First present title wins.
- **Why**: The user chose Device > Type > Global. Most-specific-wins is the least surprising precedence.

### Decision: Button Config modal — title + three-way scope + disabled Action Type placeholder
`ButtonConfigModal` shows a Button Title `Input`, a three-way scope selector (This Device / Device Type / Global), a disabled "Action Type" control labelled as coming in a later version, and OK / Cancel. OK writes the title to the selected scope's slot for that button, persists, and re-resolves the button's label; Cancel dismisses with no change.
- **Why**: This is the exact modal the user described, minus the Phase-2 action wiring. Rendering the Action Type control disabled (rather than omitting it) previews the eventual shape without implying it works.
- **Scope widget**: a `RadioSet` of three `RadioButton`s is the plain reading; final widget choice is a Phase-1 implementation detail (see Open Questions).

### Decision: In Phase 1 a click always opens config
A custom button has a title and a scope but no action, so there is nothing to run — a click opens `ButtonConfigModal`. The general rule that holds across both phases: **click runs iff the button has a runnable action; otherwise click opens config.** Phase 1 never satisfies the left branch.
- **Why**: Avoids a dead "runs nothing" click and defers the edit-gesture question to when it matters (Phase 2).

## Risks / Trade-offs

- **Empty-scope resolution edge cases** (a title saved for a device that is later deleted, or an entry with an empty string) → resolver treats missing/blank as "fall through to the next scope"; deleting a device does not need to prune the map (a stale device-id entry is simply never resolved).
- **Existing `settings.json` without `custom_buttons`** → `load` defaults the key to `{}`, exactly as `shortcuts` already does; a round-trip save then adds the key without disturbing theme or shortcuts.
- **Removing `#text`/`#text-status` may break tests that query them** → audit and update remote-screen tests as part of the change; the text-send behavior tests move to target the modal.
- **Vertical space**: five bordered buttons replace one field row but are taller; the remote already scrolls on short terminals, and the existing `test_..._does_not_scroll` baseline test guards the supported size — re-run it and adjust layout if the row pushes past the baseline.

## Migration Plan

No data migration. New installs and existing config files both work: absent `custom_buttons` loads as empty, all buttons show their `Custom N` defaults. Rollback is removing the feature; a leftover `custom_buttons` key in `settings.json` is ignored by the prior version's loader.

## Open Questions

- **Scope selector widget**: `RadioSet` vs a cycling toggle button vs `Select`. Plain reading is `RadioSet`; resolve during implementation against the modal's focus/keyboard behavior.
- **Where residual text-status messages land**: inside the text modal vs a toast (`app.notify`). Leaning toast for transient send failures, in-modal for the unsupported-text case. Confirm during implementation.
- **Deferred to Phase 2 design**: the exact edit gesture for a configured-with-action button (edit-mode key vs modifier-click, given terminal limits on long-press and alt-click).
