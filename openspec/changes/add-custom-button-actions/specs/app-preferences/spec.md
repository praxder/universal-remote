## ADDED Requirements

### Requirement: Custom button actions persisted across runs
The application SHALL persist a custom button's assigned action within the same layered custom-button structure as its title, keyed by the same scopes: a specific device (by device id), a device type (by platform identifier), and global. The action SHALL be stored inside the button's per-scope entry object alongside the title, so an entry MAY hold a title, an action, or both. Reading or writing the action MUST follow the same fault-tolerant behavior as the rest of the preferences file, and MUST NOT disturb the saved theme, shortcuts, or titles. An existing entry that holds only a title (from before actions existed) SHALL load cleanly as a button with no action.

The action shown for a given button on a given device SHALL be resolved most-specific-first — specific device, then device type, then global — independently of how the title resolves, so a button MAY use a title from one scope and an action from another.

#### Scenario: Saved action applied at startup
- **WHEN** a custom-button action was previously saved and the application restarts
- **THEN** the matching custom button runs that action when activated

#### Scenario: Action change persists to the next run
- **WHEN** the user assigns or changes a custom-button action and restarts the application
- **THEN** the application uses the changed action

#### Scenario: Most-specific action scope wins
- **WHEN** a button has an action saved both for the active device and for its device type
- **THEN** the device-specific action is used

#### Scenario: Title and action resolve independently
- **WHEN** a button has a title saved only globally and an action saved only for the active device
- **THEN** the button shows the global title and runs the device-specific action

#### Scenario: Title-only entry loads without an action
- **WHEN** the application loads a custom-button entry that holds a title but no action
- **THEN** the button shows that title and has no action to run

#### Scenario: Actions coexist with theme, shortcuts, and titles
- **WHEN** the user has a saved theme, custom shortcuts, custom-button titles, and custom-button actions
- **THEN** restarting applies all of them, and saving one does not overwrite the others
