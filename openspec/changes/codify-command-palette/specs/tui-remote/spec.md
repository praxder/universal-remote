## ADDED Requirements

### Requirement: Command palette contents
The application's command palette (opened with Ctrl+P) SHALL expose exactly the Theme, Quit, and Keys commands inherited from Textual, and SHALL NOT expose the Maximize command or the Screenshot command. Because nothing in the application maximizes a widget, the Minimize command — shown by Textual only while a widget is maximized — SHALL likewise never appear.

#### Scenario: Palette lists only the retained commands
- **WHEN** the user opens the command palette
- **THEN** its commands are exactly Theme, Quit, and Keys

#### Scenario: Maximize is excluded
- **WHEN** the user opens the command palette
- **THEN** no Maximize command is listed

#### Scenario: Screenshot is excluded
- **WHEN** the user opens the command palette
- **THEN** no Screenshot command is listed
