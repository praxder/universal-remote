## Context

Every screen today declares its hotkeys as a static `BINDINGS` class attribute with literal key strings. The home menu binds `d`/`r`/`s`/`q`; the remote binds arrows + `hjkl`, Enter, Backspace, Space, and digits, and leaves twelve keys (Volume, Channel, Mute, Menu, media transport) click-only; and each non-root screen binds `escape` to go back (the remote's `escape` also closes the session). The Settings screen has a disabled "Key Bindings (coming soon)" row. Preferences already persist to an XDG-aware `settings.json` (currently just the theme) via a fault-tolerant `PreferencesStore`.

The goal is a Keyboard Shortcuts screen that lets the user view and rebind these actions — including assigning shortcuts to the twelve keys that have none — with conflicts rejected and a toast shown, changes applied live, and choices persisted.

## Goals / Non-Goals

**Goals:**
- One catalog of rebindable actions (id, label, scope, default key) as the single source of truth for both binding and the Shortcuts table.
- View/assign/clear shortcuts from a new screen; reject conflicts and reserved keys with a toast.
- Apply changes immediately to mounted screens and persist them beside the theme.
- Assign shortcuts to remote keys that currently have none.

**Non-Goals:**
- Rebinding the D-pad directional keys (arrows/`hjkl`), Enter-activates-focused-control, or the command palette — these stay fixed (reserved). They are shown in the table as disabled rows for visibility, not edited.
- Multiple keys per action in the UI. The reserved D-pad shows both its arrow and its Vim alias, but each rebindable action holds a single key.
- Per-device or per-adapter shortcut profiles; changing the `Key` vocabulary; touching device adapters.
- Chord/sequence shortcuts — a shortcut is one normalized key.

## Decisions

### Catalog-driven `bind()`, not Textual's keymap
Textual 8.2.8 ships a keymap system (`App.set_keymap`, `Binding.id`, `BindingsMap.apply_keymap`, `handle_bindings_clash`). It confirms per-instance `self._bindings` is mutable at runtime — but `apply_keymap` only **rewrites the key of an existing binding**; it cannot introduce a binding for an action that has none. Twelve remote keys have no default binding, and the feature must let the user assign them one. So keymap alone cannot satisfy the core ask.

Decision: a `shortcuts` module exposes the action catalog and an `effective_key(action_id)` resolver (`overrides.get(id, default)`). Each catalog entry carries an `editable` flag; reserved entries (`editable=False`) have fixed keys the override map can never change. Each screen builds its own bindings on construct/mount by iterating the catalog for its scope and calling `self._bindings.bind(effective_key, action_target, id=action_id, description=label)`, skipping actions whose effective key is empty. This one mechanism handles defaults, overrides, and empties uniformly, and the same catalog + override map drives the conflict check. (Alternative — keymap for existing bindings plus `bind()` for the empties — was rejected as two mechanisms doing one job.)

### Scope-aware conflict detection
A key conflicts only when another action that can be active on the same screen already uses it. Scopes: **Home** (menu only), **Remote** (remote only), **Global** = Go Back (every screen except the root menu). Home and Remote never coexist, so they may reuse a key; Go Back overlaps Remote, so it must not collide with a remote key. The check runs against the effective map filtered to scopes that share a surface with the action being edited. (Alternative — global uniqueness across all actions — is simpler to explain but needlessly forbids harmless Home/Remote reuse and mislabels the arrow keys, which the remote D-pad legitimately shares with focus-nav.)

### Reserved entries: fixed, and shown disabled
Reserved is modeled as non-editable catalog entries (`editable=False`) rather than a hardcoded key list. The reserved entries are the four D-pad directional actions (each fixed to an arrow with an `h`/`j`/`k`/`l` alias) plus two framework entries that are not device actions — Activate Control (`enter`) and Command Palette (`ctrl+p`). The reserved-key set the assignment check uses is *derived* from these entries' keys and aliases, so there is one source of truth.

Reserved entries appear in the Shortcuts table as **disabled rows** so the user can see the key is in use but cannot capture it — the D-pad becomes visible instead of a hidden alias. A new assignment to a reserved key is rejected with a toast so the user can't brick a screen (e.g. Settings→Enter). A rebindable action's own default is exempt from the reserved and conflict checks; with the D-pad no longer rebindable, that exemption now serves exactly one case: OK defaulting to `enter`.

Note the deliberate redundancy: OK is a rebindable row showing `ENTER`, and Activate Control is a reserved row also showing `ENTER`. They describe different behaviors (the remote's OK vs. Textual activating the focused control) and both are shown per the "show every reserved key" requirement; the OK row stays editable via the default exemption.

### Unified Go Back action
The per-screen `escape`→back handlers (devices, discover, remote_flow, settings) and the remote's `escape`→exit-and-`session.close()` become one catalogued Global action, `go_back`. Its binding is added by a small shared helper (base `Screen` mixin or a `install_shortcuts()` call), but each screen keeps its own `action_go_back()` so the remote can still close the session. This is the one place where "one action" maps to per-screen behavior.

### Live apply by rebuilding mounted screens
On save, the app walks `screen_stack`, and for each screen that carries catalogued bindings calls a `rebuild_shortcuts()` that clears and re-adds its catalog bindings from the current override map, then `refresh_bindings()`. The Shortcuts screen sits above Settings above Home, so all three are mounted and pick up the change without a restart.

### Persistence: extend the existing store
`Preferences` gains `shortcuts: dict[str, str]` (action id → key); only non-default entries are stored. `PreferencesStore.load/save` read/write it alongside `theme` with the same best-effort semantics. `App.on_mount` loads it into the app's override map before pushing the menu; every save re-writes the file (theme untouched).

### Key capture, cancel, and normalization
The capture modal is a small `ModalScreen` that intercepts the next `Key` event, takes `event.key` (Textual's canonical long form, e.g. `question_mark`, `plus`), and routes it through validate → assign. **Delete** clears the shortcut; **Escape** and a **Cancel button** close the modal without changing anything. (This *reverses* an earlier plan where Escape cleared — once an explicit Cancel exists, Escape following it is the conventional keyboard cancel, and Delete remains the "delete the shortcut" gesture.) Normalization piggybacks on Textual's own long-form key names so stored keys match what `bind()` expects.

### Readable shortcut labels
The table renders a friendly, uppercase label rather than the raw stored key: `+` between a modifier and key becomes `-` (e.g. `ctrl+p` → `CTRL-P`), named keys get short forms (`space` → `SPACE`, `escape` → `ESC`, `question_mark` → `?`), and single letters uppercase (`d` → `D`). This is display-only — capture still stores and binds Textual's long form. The formatter only labels what Textual actually reports; modifiers a terminal never delivers (e.g. `cmd`) are not captured, just formatted if they ever appear.

## Risks / Trade-offs

- **Escape/Delete can't be captured as shortcuts** → Escape is the modal's cancel and Delete is its clear gesture. Acceptable: Go Back keeps `escape` as its exempt default (assigned to it, not captured through the modal), and no action needs to be *newly* bound to Escape or Delete.
- **Live rebuild touches every mounted screen** → more moving parts and test surface than apply-on-restart. Mitigation: a single `rebuild_shortcuts()` contract, exercised by tests that assign on the Shortcuts screen and assert the binding fires on the underlying screen.
- **Catalog and code drift** → the catalog must list exactly the real actions/handlers. Mitigation: a test that asserts every catalog action id resolves to a real screen action target, and every remote action maps to a `Key`.
- **Backspace stays the remote's device Back key** while `escape` is Go Back — two different "backs" that could confuse. Mitigation: they are distinct catalogued actions with distinct labels ("Back" vs "Go Back") in the table.
- **Toast on a modal** → the conflict/reserved toast must surface above the capture modal. Mitigation: `app.notify(...)` toasts render app-level, above the modal.

## Migration Plan

Purely additive; no stored-data migration. An old `settings.json` with only `theme` loads unchanged (missing `shortcuts` → empty overrides → all defaults). A downgrade ignores an unknown `shortcuts` key. Rollback = revert the change; the extra key is harmless to older builds.

## Resolved Questions

- **Modal cancel vs clear** → the modal gets an explicit **Cancel** affordance (a Cancel button and the Escape key) that closes without changing the shortcut; **Delete** clears. This reverses the earlier "Escape clears" plan (see the capture decision above) — flagged here so it's catchable in review.
- **Vim aliases on the remote** → dissolved. The premise was "if the user rebinds the D-pad." The D-pad is now **reserved and not rebindable**, so the arrows and `h`/`j`/`k`/`l` are both fixed and both shown in the table as a disabled row; nothing follows or drops.
- **Shortcut display form** → render a friendly uppercase label (e.g. `CTRL-P`, `SPACE`, `ESC`), not the raw long-form string (see the "Readable shortcut labels" decision above).
