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
- Rebinding focus-navigation (arrows/`hjkl` for moving focus), Enter-activates-focused-control, or the command palette — these stay fixed (reserved).
- Multiple keys per action in the UI. The remote D-pad keeps `hjkl` as fixed hidden aliases; the table shows and rebinds the single primary (arrow) key only.
- Per-device or per-adapter shortcut profiles; changing the `Key` vocabulary; touching device adapters.
- Chord/sequence shortcuts — a shortcut is one normalized key.

## Decisions

### Catalog-driven `bind()`, not Textual's keymap
Textual 8.2.8 ships a keymap system (`App.set_keymap`, `Binding.id`, `BindingsMap.apply_keymap`, `handle_bindings_clash`). It confirms per-instance `self._bindings` is mutable at runtime — but `apply_keymap` only **rewrites the key of an existing binding**; it cannot introduce a binding for an action that has none. Twelve remote keys have no default binding, and the feature must let the user assign them one. So keymap alone cannot satisfy the core ask.

Decision: a `shortcuts` module exposes the action catalog and an `effective_key(action_id)` resolver (`overrides.get(id, default)`). Each screen builds its own bindings on construct/mount by iterating the catalog for its scope and calling `self._bindings.bind(effective_key, action_target, id=action_id, description=label)`, skipping actions whose effective key is empty. This one mechanism handles defaults, overrides, and empties uniformly, and the same catalog + override map drives the conflict check. (Alternative — keymap for existing bindings plus `bind()` for the empties — was rejected as two mechanisms doing one job.)

### Scope-aware conflict detection
A key conflicts only when another action that can be active on the same screen already uses it. Scopes: **Home** (menu only), **Remote** (remote only), **Global** = Go Back (every screen except the root menu). Home and Remote never coexist, so they may reuse a key; Go Back overlaps Remote, so it must not collide with a remote key. The check runs against the effective map filtered to scopes that share a surface with the action being edited. (Alternative — global uniqueness across all actions — is simpler to explain but needlessly forbids harmless Home/Remote reuse and mislabels the arrow keys, which the remote D-pad legitimately shares with focus-nav.)

### Reserved keys, defaults exempt
A separate reserved set — focus-nav (`up`/`down`/`left`/`right`, `h`/`j`/`k`/`l`), `enter`, `ctrl+p` — is rejected for **new** assignments so the user can't brick a screen (e.g. Settings→Enter). Defaults are exempt: the remote Up action legitimately defaults to the Up arrow even though that key drives focus elsewhere. Enforced by exempting an action's own default from both the reserved and conflict checks.

### Unified Go Back action
The per-screen `escape`→back handlers (devices, discover, remote_flow, settings) and the remote's `escape`→exit-and-`session.close()` become one catalogued Global action, `go_back`. Its binding is added by a small shared helper (base `Screen` mixin or a `install_shortcuts()` call), but each screen keeps its own `action_go_back()` so the remote can still close the session. This is the one place where "one action" maps to per-screen behavior.

### Live apply by rebuilding mounted screens
On save, the app walks `screen_stack`, and for each screen that carries catalogued bindings calls a `rebuild_shortcuts()` that clears and re-adds its catalog bindings from the current override map, then `refresh_bindings()`. The Shortcuts screen sits above Settings above Home, so all three are mounted and pick up the change without a restart.

### Persistence: extend the existing store
`Preferences` gains `shortcuts: dict[str, str]` (action id → key); only non-default entries are stored. `PreferencesStore.load/save` read/write it alongside `theme` with the same best-effort semantics. `App.on_mount` loads it into the app's override map before pushing the menu; every save re-writes the file (theme untouched).

### Key capture and normalization
The capture modal is a small `ModalScreen` that intercepts the next `Key` event, takes `event.key` (Textual's canonical long form, e.g. `question_mark`, `plus`), and routes it through validate → assign. Delete and Escape are treated as the clear gesture (see Open Questions). Normalization piggybacks on Textual's own long-form key names so stored keys match what `bind()` expects.

## Risks / Trade-offs

- **Escape/Delete can't be captured as shortcuts** → they are the modal's clear gesture. Acceptable: Go Back keeps `escape` as its exempt default, and no action needs to be *newly* bound to Escape.
- **Live rebuild touches every mounted screen** → more moving parts and test surface than apply-on-restart. Mitigation: a single `rebuild_shortcuts()` contract, exercised by tests that assign on the Shortcuts screen and assert the binding fires on the underlying screen.
- **Catalog and code drift** → the catalog must list exactly the real actions/handlers. Mitigation: a test that asserts every catalog action id resolves to a real screen action target, and every remote action maps to a `Key`.
- **Backspace stays the remote's device Back key** while `escape` is Go Back — two different "backs" that could confuse. Mitigation: they are distinct catalogued actions with distinct labels ("Back" vs "Go Back") in the table.
- **Toast on a modal** → the conflict/reserved toast must surface above the capture modal. Mitigation: `app.notify(...)` toasts render app-level, above the modal.

## Migration Plan

Purely additive; no stored-data migration. An old `settings.json` with only `theme` loads unchanged (missing `shortcuts` → empty overrides → all defaults). A downgrade ignores an unknown `shortcuts` key. Rollback = revert the change; the extra key is harmless to older builds.

## Open Questions

- **Modal cancel vs clear**: Delete and Escape both clear (per decision), leaving no pure no-op cancel. Is that acceptable, or should the modal offer a Cancel affordance (button / a distinct key) that closes without changing the shortcut? Current plan: clear-only, no separate cancel.
- **Vim aliases on the remote**: plan keeps `hjkl` as fixed hidden aliases not shown in the table; if a user rebinds the arrow-based D-pad action, should the `hjkl` alias follow, stay, or be dropped? Current plan: alias unchanged (still `hjkl`), only the arrow rebinds.
- **Shortcut display form**: how to render special keys in the table cell (e.g. `space`, `escape`, `ctrl+p`) — raw long-form vs a friendlier label. Current plan: show the normalized long-form string.
