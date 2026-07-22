## ADDED Requirements

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
