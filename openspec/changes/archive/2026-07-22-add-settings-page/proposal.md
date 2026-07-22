## Why

The app has no place to change or persist user preferences. The command-palette
theme picker resets to the default on every launch because the app persists no
theme, and there is no home for other app-level settings (licenses, repo link,
version, future keybindings). A dedicated Settings page — reachable from the
home menu — gives these a home and introduces the persistence layer the app
currently lacks.

## What Changes

- Add a **Settings entry point** to the home menu: a "Settings" button docked in
  the bottom-left corner (home content stays centered) plus an `s` key binding.
  Either opens the Settings screen.
- Add a new **Settings screen** with a "Settings" ASCII-art banner and these rows:
  - **Theme** — invokes the built-in Textual theme picker (the same picker the
    command palette offers).
  - **Key Bindings** — a placeholder/stub row. The rebind system is a separate
    follow-up change; this row does not yet open a working rebind page.
  - **Third-party licenses** — opens the generated `THIRD_PARTY_LICENSES.md` on
    GitHub (`main`) in the browser.
  - **GitHub repo** — opens `https://github.com/praxder/universal-remote` in the browser.
  - **Version** — shows the app version; not clickable.
- Introduce a new **preferences store** (`settings.json`, XDG-aware, mirroring
  the existing device store). v1 holds one preference: the selected theme name.
- **Persist the theme across runs**: read and apply the saved theme at startup;
  save whenever the theme changes — so both the Settings-page picker and the
  existing command-palette picker now persist their selection.
- **Generate and commit** `THIRD_PARTY_LICENSES.md` from the project's
  dependencies so the licenses row's link resolves.

Out of scope (cut during exploration): clear-data/reset, changing the
preferences file location, and the keybinding rebind system (deferred).

## Capabilities

### New Capabilities
- `app-preferences`: An XDG-aware store that persists app-level user preferences
  across runs; v1 remembers the selected theme, loading it at startup and saving
  it whenever the theme changes from anywhere in the app.
- `tui-settings`: A Settings screen reached from the home menu, exposing a theme
  picker, a Key Bindings placeholder, a third-party-licenses link, a repo link,
  and a version label.

### Modified Capabilities
- `tui-remote`: The home menu gains a Settings entry point — a bottom-left
  "Settings" button and an `s` key binding — that opens the Settings screen.

## Impact

- **New code**: a preferences store module (mirroring `devices/store.py`); a
  Settings screen in `tui/`; an App-level theme watcher that persists the theme.
- **Modified code**: `tui/menu.py` (Settings button + `s` binding), `tui/app.py`
  (load/apply saved theme at startup, persist on change).
- **New repo file**: `THIRD_PARTY_LICENSES.md`, generated from dependencies.
- **New config file**: `settings.json` under `~/.config/universal-remote/`
  (or `$XDG_CONFIG_HOME`), created on first theme change.
- **No breaking changes**: existing `devices.json` and `error.log` are untouched.
