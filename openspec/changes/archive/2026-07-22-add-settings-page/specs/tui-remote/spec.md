## MODIFIED Requirements

### Requirement: Menu-driven entry with two modes
The application SHALL launch into a menu offering two modes: Manage Devices and Use Remote. Both modes MUST be reachable by keyboard and by mouse. The menu SHALL also present a Settings entry point — a "Settings" button docked in the bottom-left corner of the screen, plus an `s` key binding — that opens the Settings screen. The Settings entry point MUST be reachable by keyboard (the `s` key) and by mouse (clicking the button). Adding the Settings entry point SHALL NOT change the centered layout of the existing menu content (title, mode buttons, and movie quote).

#### Scenario: Menu offers both modes
- **WHEN** the application starts
- **THEN** it shows a menu with Manage Devices and Use Remote options

#### Scenario: Mode reachable by keyboard and mouse
- **WHEN** the user selects a mode with the keyboard or by clicking it
- **THEN** the application navigates to that mode

#### Scenario: Settings reachable by key
- **WHEN** the user presses the `s` key on the menu
- **THEN** the application opens the Settings screen

#### Scenario: Settings reachable by button
- **WHEN** the user clicks the bottom-left Settings button on the menu
- **THEN** the application opens the Settings screen
