## 1. Preferences store (spine)

- [x] 1.1 Write tests for `PreferencesStore`: default path honors `$XDG_CONFIG_HOME` then falls back to `~/.config/universal-remote/settings.json`; `load()` on a missing file returns defaults; `load()` on a corrupt/unparseable file returns defaults (no raise); `save()` then `load()` round-trips the theme name
- [x] 1.2 Implement `PreferencesStore` in a new module mirroring `devices/store.py`: `default_settings_path()`, fault-tolerant `load()`, indented-JSON `save()`, v1 schema `{ "theme": "<name>" }`
- [x] 1.3 Run the new store tests green

## 2. Theme persistence wiring

- [x] 2.1 Write a TUI test: changing `app.theme` writes the new theme name to `settings.json` (covers both command-palette and settings-picker paths, since both set `app.theme`)
- [x] 2.2 Write a TUI test: launching the app with a saved theme applies it; launching with an unknown/absent saved theme uses the default and does not error
- [x] 2.3 Add `watch_theme` to `UniversalRemoteApp` that persists the theme via `PreferencesStore`; give the app a `PreferencesStore` instance (constructor-injectable, like `store`, for testing)
- [x] 2.4 In `on_mount`, before pushing `MenuScreen`, load the saved theme and apply it only if present in `self.available_themes`
- [x] 2.5 Run the theme-persistence tests green

## 3. Settings screen

- [x] 3.1 Write tests for `SettingsScreen`: it mounts with a "Settings" banner; the Theme row invokes the app's theme picker; the licenses and repo rows open the expected URLs (assert via an injected/patched opener, not a real browser); the Key Bindings row is a non-navigating placeholder; the version label shows `version("universal-remote")` and is not focusable; escape/q returns to the menu
- [x] 3.2 Create `SettingsScreen` in a new `tui/settings_screen.py` with the "Settings" ASCII banner and the rows (theme, key-bindings placeholder, licenses, repo, version)
- [x] 3.3 Wire the Theme row to `self.app.search_themes()`
- [x] 3.4 Wire the licenses and repo rows to open their URLs via a small, injectable open-URL helper (default `webbrowser.open`) so tests can assert without launching a browser
- [x] 3.5 Render the version label as a non-interactive `Static` (`can_focus=False`) from package metadata
- [x] 3.6 Add the "Settings" banner and row CSS to the app's stylesheet, matching the existing banner pattern
- [x] 3.7 Run the settings-screen tests green

## 4. Home-menu entry point

- [x] 4.1 Write tests for `MenuScreen`: pressing `s` opens the Settings screen; clicking the bottom-left Settings button opens it; the existing Manage Devices / Use Remote / Quit bindings and centered layout are unchanged
- [x] 4.2 Add the `s` → `action_settings` binding and a bottom-left "Settings" button to `MenuScreen`; route the button click through `on_button_pressed`
- [x] 4.3 Add CSS docking the Settings button to the bottom-left above the `Footer` without disturbing the centered title/buttons/quote
- [x] 4.4 Run the menu tests green

## 5. Third-party licenses file

- [x] 5.1 Generate `THIRD_PARTY_LICENSES.md` from dependencies (`pip-licenses --format=markdown` via `uvx`/dev tooling) and commit it at the repo root
- [x] 5.2 Confirm the Settings licenses link targets `https://github.com/praxder/universal-remote/blob/main/THIRD_PARTY_LICENSES.md`

## 6. Verification & docs

- [x] 6.1 Visually verify the home screen: export a screenshot and confirm the Settings button sits bottom-left, above the footer, with the centered content unchanged and the footer hints not clipped
- [x] 6.2 Visually verify the Settings screen: banner, all rows, and version label render correctly
- [x] 6.3 Update in-repo docs (README or equivalent) to mention the Settings page, the `s` shortcut, and how to regenerate `THIRD_PARTY_LICENSES.md`
- [x] 6.4 Preflight: format, lint/type-check, and run the full test suite; fix any failures
