## Context

The TUI (Textual) launches into `MenuScreen` and persists nothing about the
user's preferences. `App.theme` is a Textual `Reactive[str]` defaulting to
`constants.DEFAULT_THEME`; the command palette's theme picker sets it for the
session only. Device data lives in `devices/store.py` (`DeviceStore`), an
XDG-aware JSON store at `~/.config/universal-remote/devices.json`. This change
adds a parallel preferences store, a Settings screen, and a home-menu entry
point, and wires theme changes to persist. Keybinding rebinding, clear/reset,
and file relocation are explicitly deferred/cut.

## Goals / Non-Goals

**Goals:**
- A `PreferencesStore` that mirrors `DeviceStore`'s pattern and semantics.
- Theme selection persists across runs, no matter where it is changed
  (Settings screen or command palette).
- A Settings screen reachable from home by an `s` key and a bottom-left button,
  exposing theme, a keybindings placeholder, licenses/repo links, and version.
- A committed `THIRD_PARTY_LICENSES.md` so the licenses link resolves.

**Non-Goals:**
- Keybinding rebinding (separate follow-up change; only a placeholder row here).
- Clear-data/reset and preferences-file relocation (cut).
- Persisting any preference other than the theme in this version.

## Decisions

### Preferences persistence: a new `PreferencesStore`
Add `src/universal_remote/preferences/store.py` (or `devices`-sibling module)
mirroring `DeviceStore`: a `default_settings_path()` using the same
`$XDG_CONFIG_HOME` → `~/.config` fallback, resolving to
`universal-remote/settings.json`; a `PreferencesStore` class with `load()`
returning a small preferences object/dict and `save()` writing indented JSON.
v1 schema: `{ "theme": "<name>" }`. Reads are fault-tolerant — a missing or
unparseable file yields defaults rather than raising, so a corrupt file never
blocks startup.
- *Why mirror DeviceStore*: consistency, an established tested pattern, same
  location convention. *Alternative*: extend DeviceStore to also hold prefs —
  rejected; conflates device data with app prefs and complicates the existing
  0600 device file.

### Theme persistence hook: public `watch_theme` on the App
`UniversalRemoteApp` defines `def watch_theme(self, theme_name: str) -> None`
that writes the new theme to `PreferencesStore`. Textual's reactive dispatch
(`reactive.py`) invokes both the framework's private `_watch_theme` and a
subclass's public `watch_theme`, so overriding the public watcher persists on
every theme change — whether triggered by the Settings picker or the command
palette — without touching Textual internals.
- *Alternative considered*: subscribe to `App.theme_changed_signal`. Equally
  valid and slightly more decoupled; the public watcher is chosen for being the
  simplest single-method addition. Noted as a fallback if the watcher proves
  fragile across Textual versions.

### Applying the saved theme at startup
In `on_mount`, before `push_screen(MenuScreen())`, read the saved theme and, if
it is present in `self.available_themes`, assign `self.theme`. An unknown name
(e.g. a theme removed by a Textual upgrade) is ignored and the default stands —
guarding against `_validate_theme` raising on an unregistered theme. Assigning
a valid saved theme re-fires `watch_theme` and rewrites the identical value;
this is idempotent and only touches an already-existing file, so fresh installs
that never change the theme create no `settings.json`.

### Settings screen
New `src/universal_remote/tui/settings_screen.py` with `SettingsScreen(Screen)`:
- A "Settings" ASCII-art banner (`#settings-title`, accent-colored), matching
  the existing banner CSS pattern in `app.py`.
- Rows as focusable `Button`s: **Theme** → `self.app.search_themes()`;
  **Third-party licenses** and **GitHub repo** → `webbrowser.open(url)`;
  **Key Bindings** → a disabled button (or "(coming soon)" label) that performs
  no navigation.
- **Version** as a non-interactive `Static` (`can_focus=False`) reading
  `importlib.metadata.version("universal-remote")` — the same source `cli.py`
  already uses (the frozen binary reads the stamped `pyproject`).
- Back to menu via an `escape`/`q` binding calling `self.app.pop_screen()`.

### Home-menu entry point
`MenuScreen` gains an `("s", "settings", "Settings")` binding and an
`action_settings` that pushes `SettingsScreen`, plus a bottom-left "Settings"
`Button`. The button is placed in a container docked to the bottom (above the
`Footer`, which docks last), left-aligned, so the centered title/buttons/quote
are unaffected. Click routes through `on_button_pressed` to `action_settings`.

### Third-party licenses file
Generate `THIRD_PARTY_LICENSES.md` from installed dependencies with
`pip-licenses --format=markdown` (run via `uvx`/dev tooling) and commit it at
the repo root. Regeneration is manual when dependencies change (documented in
the tasks). The Settings link targets
`https://github.com/praxder/universal-remote/blob/main/THIRD_PARTY_LICENSES.md`.

## Risks / Trade-offs

- **Bottom-left button vs. Footer and centered layout** → Textual dock ordering
  can surprise; verify visually with a screenshot (export_screenshot → PNG →
  view) that the button sits above the footer, left-aligned, and the centered
  content is unchanged. Adding an `s` footer hint keeps the menu at 4 shown
  keys (d, r, s, q) — under the ~8-hint/80-col clip threshold.
- **Public `watch_theme` relies on Textual's private+public watcher dispatch**
  → verified in the pinned Textual version; if a future upgrade changes it,
  switch to `theme_changed_signal`. Covered by a test asserting a theme change
  writes `settings.json`.
- **Saved theme name drift** (renamed/removed theme) → guarded by the
  `available_themes` membership check; falls back to default.
- **`THIRD_PARTY_LICENSES.md` goes stale** as dependencies change → acceptable
  for v1; manual regeneration step documented. Not wired into CI here.
- **`webbrowser.open` in a TUI** → spawns the OS default browser; on headless
  environments it may no-op, which is acceptable for a local desktop app.
