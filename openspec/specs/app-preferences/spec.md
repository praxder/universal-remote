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
