## ADDED Requirements

### Requirement: Macros persisted across runs
The application SHALL persist the saved macros in the same preferences file as the theme,
the custom shortcuts, and the custom buttons. The stored macro registry SHALL hold each
macro under its stable identifier, together with the macro's name and its ordered steps,
and SHALL hold the default-name counter alongside them so numbering survives a restart.
Reading or writing macros MUST follow the same fault-tolerant behavior as the rest of the
preferences file: a missing, malformed, or non-object macro registry SHALL load as no
saved macros rather than raising, and an unwritable configuration directory SHALL be
ignored rather than crashing the application.

Saving any one preference SHALL preserve all the others. In particular, persisting the
theme, a shortcut, or a custom button SHALL NOT drop the saved macros, and saving a macro
SHALL NOT disturb the saved theme, shortcuts, or custom buttons.

#### Scenario: Saved macros available at startup
- **WHEN** the user recorded a macro in an earlier run and the application restarts
- **THEN** the macros list shows that macro with its name and steps

#### Scenario: Macro edits persist to the next run
- **WHEN** the user renames a macro or changes its steps, saves, and restarts the application
- **THEN** the macros list shows the changed name and steps

#### Scenario: A deleted macro stays deleted
- **WHEN** the user deletes a macro and restarts the application
- **THEN** the macros list no longer shows it

#### Scenario: The default-name counter survives a restart
- **WHEN** the user has recorded two macros, restarts the application, and records another without renaming it
- **THEN** the new macro is named `Macro 3`

#### Scenario: Changing the theme does not erase macros
- **WHEN** the user has saved macros and then changes the application theme
- **THEN** the saved macros are still present, both immediately and after a restart

#### Scenario: Macros coexist with theme, shortcuts, and custom buttons
- **WHEN** the user has a saved theme, custom shortcuts, custom-button titles and actions, and saved macros
- **THEN** restarting applies all of them, and saving one does not overwrite the others

#### Scenario: A malformed macro registry loads as none
- **WHEN** the preferences file holds a macro registry that is missing or is not an object
- **THEN** the application starts with no saved macros and does not raise

#### Scenario: An unwritable configuration directory is ignored
- **WHEN** saving a macro fails because the configuration directory cannot be written
- **THEN** the failure is ignored and the application continues rather than crashing
