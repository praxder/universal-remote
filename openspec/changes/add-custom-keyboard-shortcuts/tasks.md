## 1. Action catalog + effective-key resolver

- [ ] 1.1 Add a failing test `tests/test_shortcuts_catalog.py`: the catalog lists the 4 Home actions (`d`/`r`/`s`/`q`), the Global `go_back` (`escape`), and 30 Remote actions (29 `Key` members + `text`), each with id, label, scope, and default key; the 12 click-only remote keys default to no key.
- [ ] 1.2 Add a failing test: every Remote action id maps to a real `Key` enum member, and every catalog action has a unique id.
- [ ] 1.3 Create `src/universal_remote/tui/shortcuts.py` with a `Scope` enum (`HOME`/`GLOBAL`/`REMOTE`), an `Action` dataclass `(id, label, scope, default_key, target)`, the `CATALOG` list, and `effective_key(action_id, overrides)` returning `overrides.get(id, default)`.
- [ ] 1.4 Add `conflicts(action_id, key, overrides)` and `is_reserved(action_id, key)` helpers: reserved = arrows + `hjkl` + `enter` + `ctrl+p`, exempting the action's own default; conflict = scope-aware (Home/Remote may reuse, Global overlaps Remote).
- [ ] 1.5 Add failing tests for 1.4: same-scope reuse rejected, Home↔Remote reuse allowed, `go_back` vs a remote key rejected, reserved key rejected, an action's default is exempt. Run tasks 1.1–1.5 green.

## 2. Persist shortcuts in preferences

- [ ] 2.1 Add a failing test in `tests/test_preferences_store.py`: saving `Preferences(theme=…, shortcuts={"remote.vol_up": "="})` round-trips both fields, and loading an old file with only `theme` yields empty `shortcuts`.
- [ ] 2.2 Add `shortcuts: dict[str, str]` (default empty) to the `Preferences` dataclass in `src/universal_remote/preferences/store.py`.
- [ ] 2.3 Update `PreferencesStore.load`/`save` to read/write `shortcuts` alongside `theme`, keeping the best-effort (never-raise) semantics; only non-default entries are written. Run tasks 2.1–2.2 green.

## 3. Build screen bindings from the catalog

- [ ] 3.1 Add a failing test in `tests/test_tui_remote_surface.py`: with an override assigning a formerly-unbound key (e.g. Volume Up → `=`), pressing it on the remote sends that `Key` on a supporting adapter.
- [ ] 3.2 Add a `rebuild_shortcuts(overrides)` helper (shared mixin or module function) that clears an instance's catalog bindings and re-adds, via `self._bindings.bind(key, target, id=…, description=label)`, every catalog action for the screen's scope whose effective key is non-empty, then calls `refresh_bindings()`.
- [ ] 3.3 Use the helper in `MenuScreen` (Home scope incl. Quit) and `RemoteScreen` (Remote scope incl. Text), reading overrides from `self.app`, replacing the hardcoded literal `BINDINGS` for catalogued actions (keep focus-nav `hjkl`/arrows and the D-pad `hjkl` aliases as fixed bindings).
- [ ] 3.4 Add a failing test: assigning a Home action a custom key triggers it on the menu and the default no longer fires. Run 3.1–3.4 green.

## 4. Unified Go Back action

- [ ] 4.1 Add failing tests: `escape` (the `go_back` default) still returns from Devices, Discover, Use-Remote picker, and Settings; on the remote it still closes the session and pops.
- [ ] 4.2 Add `go_back` to the shortcut build so every non-root screen binds its effective key to a per-screen `action_go_back()`; keep the remote's handler closing the session before popping.
- [ ] 4.3 Add a failing test: rebinding `go_back` to another key returns a page with the new key and `escape` no longer does. Run 4.1–4.3 green.

## 5. Keyboard Shortcuts screen + capture modal

- [ ] 5.1 Add a failing test `tests/test_tui_shortcuts.py`: opening the screen shows a table with a row per catalog action and its current shortcut (blank when none).
- [ ] 5.2 Add failing tests: Enter on a row opens the capture modal; pressing an available key assigns it (row updates, persisted); pressing Delete or Escape clears it.
- [ ] 5.3 Add failing tests: assigning a taken key (same-scope or `go_back` vs remote) is refused, leaves the shortcut unchanged, and shows an error toast; assigning a reserved key is refused with a toast.
- [ ] 5.4 Create `src/universal_remote/tui/shortcuts_screen.py`: a `ShortcutsScreen` with a `DataTable` (Action | Shortcut) built from the catalog + app overrides, and a `CaptureModal` `ModalScreen` that reads the next key, routes through `is_reserved`/`conflicts`, and on success updates overrides + persists + rebuilds mounted screens (Delete/Escape → clear).
- [ ] 5.5 On any assign/clear, save via `PreferencesStore` and call `rebuild_shortcuts` across `self.app.screen_stack`. Run 5.1–5.3 green.

## 6. Wire Settings entry + startup application

- [ ] 6.1 Add a failing test in `tests/test_tui_settings.py`: the Keyboard Shortcuts row is enabled and opens `ShortcutsScreen`.
- [ ] 6.2 In `settings_screen.py`, enable the `#keybindings` row (relabel "Keyboard Shortcuts"), and push `ShortcutsScreen` on activation.
- [ ] 6.3 Add a failing test in `tests/test_tui_theme_persistence.py` (or a new startup test): a saved `shortcuts` map is loaded and applied so a custom key works from launch.
- [ ] 6.4 In `app.py` `__init__`/`on_mount`, load `preferences.shortcuts` into an app-level override map and apply it before/at menu push. Run 6.1–6.3 green.

## 7. Docs + preflight

- [ ] 7.1 Update `README.md` and any key-binding docs to mention customizable shortcuts and the Settings entry.
- [ ] 7.2 Refresh the Settings screenshot if the row label changed; add a Keyboard Shortcuts screenshot.
- [ ] 7.3 Run formatter, linter, and the full test suite; fix any failures.
- [ ] 7.4 Manually exercise: open Shortcuts from Settings, assign a formerly-unbound remote key and confirm it works live, hit a conflict and a reserved key (toast shown), clear a shortcut, restart and confirm persistence.
