# app-preferences Specification

## Purpose
TBD - created by syncing change add-settings-page. Update Purpose after archive.
## Requirements
### Requirement: Preferences persisted across runs
The application SHALL persist app-level user preferences to an XDG-aware JSON file at `$XDG_CONFIG_HOME/universal-remote/settings.json`, falling back to `~/.config/universal-remote/settings.json` when `XDG_CONFIG_HOME` is unset, mirroring the existing device store's location convention. The file SHALL be created on first write and MUST NOT disturb the existing `devices.json` or `error.log`. When the file is absent or unreadable, the application SHALL fall back to built-in defaults rather than failing to start.

#### Scenario: Preferences file lives beside the device store
- **WHEN** a preference is saved and `XDG_CONFIG_HOME` is set
- **THEN** it is written to `$XDG_CONFIG_HOME/universal-remote/settings.json`

#### Scenario: Falls back to the home config directory
- **WHEN** a preference is saved and `XDG_CONFIG_HOME` is unset
- **THEN** it is written to `~/.config/universal-remote/settings.json`

#### Scenario: Missing preferences file uses defaults
- **WHEN** the application starts and no `settings.json` exists
- **THEN** it starts normally using built-in default preferences and does not error

### Requirement: Selected theme remembered across runs
The application SHALL remember the selected theme. On startup it SHALL load the saved theme and apply it before the menu is shown; when no theme is saved it SHALL use the built-in default theme. Whenever the theme changes from anywhere in the application — the Settings screen or the command palette — the new theme SHALL be saved to the preferences file so it persists to the next run.

#### Scenario: Saved theme applied at startup
- **WHEN** a theme was previously selected and the application restarts
- **THEN** the application launches with that theme applied

#### Scenario: Theme change from the command palette persists
- **WHEN** the user changes the theme via the command palette and restarts the application
- **THEN** the application launches with the theme chosen in the command palette

#### Scenario: Theme change from the Settings screen persists
- **WHEN** the user changes the theme from the Settings screen and restarts the application
- **THEN** the application launches with the theme chosen on the Settings screen

#### Scenario: Default theme when none saved
- **WHEN** the application starts with no saved theme
- **THEN** it applies the built-in default theme

### Requirement: Custom keyboard shortcuts persisted across runs

The application SHALL persist the user's custom keyboard shortcuts in the same preferences file as the theme, as a map of action identifier to key string. Only shortcuts that differ from an action's default SHALL need to be stored. On startup the application SHALL load the saved shortcuts and apply them to its bindings before the menu is shown; when no custom shortcuts are saved it SHALL use the catalog's default keys. Reading or writing the shortcuts map MUST follow the same fault-tolerant behavior as the rest of the preferences file: a missing or unreadable file SHALL fall back to defaults rather than failing to start, and an unwritable file SHALL be ignored rather than raised. Persisting shortcuts MUST NOT disturb the saved theme.

#### Scenario: Saved shortcut applied at startup

- **WHEN** a custom shortcut was previously assigned and the application restarts
- **THEN** the application launches with that shortcut active on the relevant screen

#### Scenario: Shortcut change persists to the next run

- **WHEN** the user assigns or clears a shortcut and restarts the application
- **THEN** the application launches with the changed shortcut

#### Scenario: Shortcuts and theme coexist

- **WHEN** the user has both a saved theme and custom shortcuts
- **THEN** restarting the application applies both, and saving one does not overwrite the other

#### Scenario: Missing shortcuts use defaults

- **WHEN** the application starts and no custom shortcuts are saved
- **THEN** every action uses its catalog default key and the application does not error
