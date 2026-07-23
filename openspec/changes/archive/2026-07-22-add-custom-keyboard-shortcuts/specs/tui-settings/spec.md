## MODIFIED Requirements

### Requirement: Key Bindings placeholder row
The Settings screen SHALL present a Keyboard Shortcuts row that, when activated, opens the Keyboard Shortcuts screen (see the keyboard-shortcuts capability). The row MUST be reachable by keyboard and by mouse, consistent with the other Settings rows, and SHALL no longer be disabled or labeled as unavailable.

#### Scenario: Keyboard Shortcuts row opens the screen
- **WHEN** the user activates the Keyboard Shortcuts row
- **THEN** the application opens the Keyboard Shortcuts screen

#### Scenario: Keyboard Shortcuts row is enabled
- **WHEN** the user views the Settings screen
- **THEN** the Keyboard Shortcuts row is shown as an enabled, activatable row
