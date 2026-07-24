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

### Requirement: Custom button titles persisted across runs
The application SHALL persist custom-button titles in the same preferences file as the theme and shortcuts, under a layered structure keyed by scope: a specific device (by device id), a device type (by platform identifier), and global. Each button is identified by its 1-based position (1 through 5), and each stored entry SHALL be an object holding at least a title, so later versions MAY extend an entry without changing the file's shape. On startup the application SHALL load the saved titles; reading or writing them MUST follow the same fault-tolerant behavior as the rest of the preferences file — a missing or unreadable file SHALL fall back to defaults rather than failing to start, and an unwritable file SHALL be ignored rather than raised. Persisting custom-button titles MUST NOT disturb the saved theme or the saved shortcuts.

The title shown for a given button on a given device SHALL be resolved most-specific-first: the entry for that specific device if present, otherwise the entry for that device's type if present, otherwise the global entry if present, otherwise the built-in default `Custom N`. An absent or blank title at one scope SHALL fall through to the next less-specific scope.

When a saved device is deleted, the application SHALL remove that device's device-scoped custom-button entries from the preferences, leaving the device-type and global entries for those buttons intact. Removing them MUST follow the same fault-tolerant, best-effort persistence behavior as the rest of the preferences file.

#### Scenario: Saved title applied at startup
- **WHEN** a custom-button title was previously saved and the application restarts
- **THEN** the application shows that title on the matching custom button

#### Scenario: Title change persists to the next run
- **WHEN** the user saves or changes a custom-button title and restarts the application
- **THEN** the application shows the changed title

#### Scenario: Most-specific scope wins
- **WHEN** a button has a title saved both for the active device and for its device type
- **THEN** the device-specific title is shown

#### Scenario: Falls through to a less specific scope
- **WHEN** a button has no title for the active device but has one saved for its device type
- **THEN** the device-type title is shown

#### Scenario: Default when no scope matches
- **WHEN** a button has no title saved at any scope for the active device
- **THEN** the button shows its `Custom N` default

#### Scenario: Titles, theme, and shortcuts coexist
- **WHEN** the user has a saved theme, custom shortcuts, and custom-button titles
- **THEN** restarting applies all three, and saving one does not overwrite the others

#### Scenario: Missing custom buttons use defaults
- **WHEN** the application starts and no custom-button titles are saved
- **THEN** every custom button shows its `Custom N` default and the application does not error

#### Scenario: Deleting a device removes its device-scoped titles
- **WHEN** a button has a title saved for a specific device and that device is deleted
- **THEN** that device-scoped entry is removed while any device-type and global titles for that button remain

### Requirement: Custom button actions persisted across runs
The application SHALL persist a custom button's assigned action within the same layered custom-button structure as its title, keyed by the same scopes: a specific device (by device id), a device type (by platform identifier), and global. The action SHALL be stored inside the button's per-scope entry object alongside the title, so an entry MAY hold a title, an action, or both. Reading or writing the action MUST follow the same fault-tolerant behavior as the rest of the preferences file, and MUST NOT disturb the saved theme, shortcuts, or titles. An existing entry that holds only a title (from before actions existed) SHALL load cleanly as a button with no action.

The action shown for a given button on a given device SHALL resolve from the same scope as the title: the button's stored entry SHALL resolve as a single unit, most-specific-first — specific device, then device type, then global — so a button's title and action are always taken together from the same scope and never split across scopes.

#### Scenario: Saved action applied at startup
- **WHEN** a custom-button action was previously saved and the application restarts
- **THEN** the matching custom button runs that action when activated

#### Scenario: Action change persists to the next run
- **WHEN** the user assigns or changes a custom-button action and restarts the application
- **THEN** the application uses the changed action

#### Scenario: Most-specific action scope wins
- **WHEN** a button has an action saved both for the active device and for its device type
- **THEN** the device-specific action is used

#### Scenario: Title and action resolve from the same scope
- **WHEN** the active device's entry holds both a title and an action, while only a title is saved globally
- **THEN** the button uses the device entry's title and action together, and the global title is not mixed in

#### Scenario: Title-only entry loads without an action
- **WHEN** the application loads a custom-button entry that holds a title but no action
- **THEN** the button shows that title and has no action to run

#### Scenario: Actions coexist with theme, shortcuts, and titles
- **WHEN** the user has a saved theme, custom shortcuts, custom-button titles, and custom-button actions
- **THEN** restarting applies all of them, and saving one does not overwrite the others

