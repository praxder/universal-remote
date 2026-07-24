## 1. Action catalog + effective-key resolver

- [x] 1.1 Add a failing test `tests/test_shortcuts_catalog.py`: the catalog lists the 4 rebindable Home actions (`d`/`r`/`s`/`q`), the Global `go_back` (`escape`), and 26 rebindable Remote actions (25 `Key` members + `text`), each with id, label, scope, and default key; the 12 click-only remote keys default to no key.
- [x] 1.2 Add a failing test: the catalog also lists the reserved entries — the 4 D-pad directional actions (arrow key + `hjkl` alias each) and the two framework entries Activate Control (`enter`) and Command Palette (`ctrl+p`) — each marked non-editable; every device action maps to a real `Key` enum member (framework entries map to none), and every entry id is unique.
- [x] 1.3 Create `src/universal_remote/tui/shortcuts.py` with a `Scope` enum (`HOME`/`GLOBAL`/`REMOTE`), an `Action` dataclass `(id, label, scope, default_key, target, editable=True, aliases=())`, the `CATALOG` list (rebindable + reserved entries), and `effective_key(action_id, overrides)` returning `overrides.get(id, default)` (reserved entries ignore overrides).
- [x] 1.4 Add `conflicts(action_id, key, overrides)` and `is_reserved(key)` helpers: the reserved-key set is *derived* from the keys and aliases of the non-editable catalog entries; the conflict check is scope-aware (Home/Remote may reuse, Global overlaps Remote) and exempts an action's own default from both checks.
- [x] 1.5 Add failing tests for 1.4: same-scope reuse rejected, Home↔Remote reuse allowed, `go_back` vs a remote key rejected, a reserved key (`j`, `enter`, `ctrl+p`) rejected, and an action's default exempt (OK keeps `enter`). Run tasks 1.1–1.5 green.
- [x] 1.6 Add a failing test for a `display_label(key)` formatter (`ctrl+p` → `CTRL-P`, `space` → `SPACE`, `escape` → `ESC`, `d` → `D`, empty → blank); implement it in `shortcuts.py`. Run green.

## 2. Persist shortcuts in preferences

- [x] 2.1 Add a failing test in `tests/test_preferences_store.py`: saving `Preferences(theme=…, shortcuts={"remote.vol_up": "="})` round-trips both fields, and loading an old file with only `theme` yields empty `shortcuts`.
- [x] 2.2 Add `shortcuts: dict[str, str]` (default empty) to the `Preferences` dataclass in `src/universal_remote/preferences/store.py`.
- [x] 2.3 Update `PreferencesStore.load`/`save` to read/write `shortcuts` alongside `theme`, keeping the best-effort (never-raise) semantics; only non-default entries are written. Run tasks 2.1–2.2 green.

## 3. Build screen bindings from the catalog

- [x] 3.1 Add a failing test in `tests/test_tui_remote_surface.py`: with an override assigning a formerly-unbound key (e.g. Volume Up → `=`), pressing it on the remote sends that `Key` on a supporting adapter.
- [x] 3.2 Add a `rebuild_shortcuts(overrides)` helper (shared mixin or module function) that clears an instance's catalog bindings and re-adds, via `self._bindings.bind(key, target, id=…, description=label)`, every catalog action for the screen's scope whose effective key is non-empty, then calls `refresh_bindings()`.
- [x] 3.3 Use the helper in `MenuScreen` (Home scope incl. Quit) and `RemoteScreen` (Remote scope incl. Text), reading overrides from `self.app`, replacing the hardcoded literal `BINDINGS` for catalogued actions. The reserved D-pad directional entries bind their fixed arrow keys and `hjkl` aliases and never consult overrides.
- [x] 3.4 Add a failing test: assigning a Home action a custom key triggers it on the menu and the default no longer fires. Run 3.1–3.4 green.

## 4. Unified Go Back action

- [x] 4.1 Add failing tests: `escape` (the `go_back` default) still returns from Devices, Discover, Use-Remote picker, and Settings; on the remote it still closes the session and pops.
- [x] 4.2 Add `go_back` to the shortcut build so every non-root screen binds its effective key to a per-screen `action_go_back()`; keep the remote's handler closing the session before popping.
- [x] 4.3 Add a failing test: rebinding `go_back` to another key returns a page with the new key and `escape` no longer does. Run 4.1–4.3 green.

## 5. Keyboard Shortcuts screen + capture modal

- [x] 5.1 Add a failing test `tests/test_tui_shortcuts.py`: opening the screen shows a table with a row per catalog entry and its shortcut rendered via `display_label` (blank when none); reserved entries (D-pad, Activate Control, Command Palette) appear as disabled rows that cannot be activated.
- [x] 5.2 Add failing tests: Enter on a rebindable row opens the capture modal; pressing an available key assigns it (row updates, persisted); pressing Delete clears it; pressing Escape or clicking Cancel closes the modal leaving the shortcut unchanged.
- [x] 5.3 Add failing tests: assigning a taken key (same-scope or `go_back` vs remote) is refused, leaves the shortcut unchanged, and shows an error toast; assigning a reserved key is refused with a toast.
- [x] 5.4 Create `src/universal_remote/tui/shortcuts_screen.py`: a `ShortcutsScreen` with a `DataTable` (Action | Shortcut) built from the catalog + app overrides (reserved rows shown disabled, shortcuts formatted via `display_label`), and a `CaptureModal` `ModalScreen` with a Cancel button that reads the next key, routes through `is_reserved`/`conflicts`, and on success updates overrides + persists + rebuilds mounted screens (Delete → clear; Escape/Cancel → close with no change).
- [x] 5.5 On any assign/clear, save via `PreferencesStore` and call `rebuild_shortcuts` across `self.app.screen_stack`. Run 5.1–5.3 green.

## 6. Wire Settings entry + startup application

- [x] 6.1 Add a failing test in `tests/test_tui_settings.py`: the Keyboard Shortcuts row is enabled and opens `ShortcutsScreen`.
- [x] 6.2 In `settings_screen.py`, enable the `#keybindings` row (relabel "Keyboard Shortcuts"), and push `ShortcutsScreen` on activation.
- [x] 6.3 Add a failing test in `tests/test_tui_theme_persistence.py` (or a new startup test): a saved `shortcuts` map is loaded and applied so a custom key works from launch.
- [x] 6.4 In `app.py` `__init__`/`on_mount`, load `preferences.shortcuts` into an app-level override map and apply it before/at menu push. Run 6.1–6.3 green.

## 7. Docs + preflight

- [x] 7.1 Update `README.md` and any key-binding docs to mention customizable shortcuts and the Settings entry.
- [x] 7.2 Refresh the Settings screenshot if the row label changed; add a Keyboard Shortcuts screenshot.
- [x] 7.3 Run formatter, linter, and the full test suite; fix any failures.
- [x] 7.4 Manually exercise: open Shortcuts from Settings, assign a formerly-unbound remote key and confirm it works live, hit a conflict and a reserved key (toast shown), clear a shortcut, restart and confirm persistence.

## 8. Revisions (global shortcuts, ESC-assignable, Tab reserved, ASCII header, palette view)

> These reverse/extend decisions from sections 1–6; the shipped code (27/29) needs rework. Fix the tests that now assert the old behavior as you go.

- [x] 8.1 **Global conflicts.** Remove `Scope`-based overlap from `shortcuts.py`: delete `_OVERLAP`, make `conflicting_label` scan all editable actions (excluding self + own default). Keep the `scope`/surface field only for per-screen target binding. Invert `tests/test_shortcuts_catalog.py::test_given_a_home_key_reused_on_the_remote_when_checked_then_it_is_allowed` (now conflicts) and replace the `test_tui_shortcuts.py` same-scope framing with a global-uniqueness assertion.
- [x] 8.2 **Tab + bare modifiers reserved.** Add `Focus Next` (`tab`) and `Focus Previous` (`shift+tab`) as `editable=False, target=None` catalog entries (like Activate Control). `RESERVED_KEYS` derives them; add a catalog test that `tab`/`shift+tab` are reserved and a modal test that assigning Tab is refused with a toast. Also add `is_bare_modifier()` (rejects a lone `shift`/`ctrl`/`alt`/`super`/`meta`/`hyper`) and reject it in the capture modal with a toast.
- [x] 8.3 **ESC assignable + mouse-only exits.** In `CaptureModal`: remove the `escape`→cancel and `delete`→clear key handling so every key (incl. `escape`, `delete`) routes through `_assign`. Add a mouse-only **DEL** button (`can_focus = False`) that clears; keep the mouse-only **Cancel** button. Update `tests/test_tui_shortcuts.py`: `..._escape_is_pressed_then_the_shortcut_is_unchanged` → escape is assigned; `..._delete_is_pressed_then_the_shortcut_is_cleared` → clear via a DEL-button click; keep the Cancel-button test.
- [x] 8.4 **Modal padding.** Increase `#capture` interior padding and the vertical spacing between prompt, hint, and button row (CSS-only in `shortcuts_screen.py`).
- [x] 8.5 **ASCII banner.** Replace `Static("Keyboard Shortcuts")` with a `TITLE_ART` raw-string banner + matching `#shortcuts-title` width CSS in `app.py`, following `menu.py`/`settings_screen.py`. Verify visually (export_screenshot → PNG → view) at 80 cols so it does not wrap.
- [x] 8.6 **Command palette view.** Add an `App.COMMANDS` provider yielding one "Keyboard Shortcuts" command that dismisses the palette and pushes a read-only `ModalScreen` (a `DataTable` of Action | Shortcut formatted via `display_label`, no capture). Tests: the command exists; selecting it opens the modal; the modal has no editable affordance.
- [x] 8.7 Run formatter, linter, and the full test suite; fix failures. Re-do the manual pass in 7.4 covering ESC-assign, Tab-refused, DEL-button clear, the palette view, and a cross-surface conflict now being rejected.
- [x] 8.8 **Group the table by surface.** `_populate_shortcuts_table` builds the one `DataTable` with a bold `HOME`/`GLOBAL`/`REMOTE` heading row (and a spacer) before each group; heading/spacer rows carry sentinel keys and are non-activatable. Shared by `ShortcutsScreen` and the read-only `ShortcutsViewModal`. Tests: every action still listed, each group header present, activating a header opens no modal.
