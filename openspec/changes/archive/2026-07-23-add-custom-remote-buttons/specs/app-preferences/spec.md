## ADDED Requirements

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
