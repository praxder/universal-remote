## ADDED Requirements

### Requirement: Reject duplicate name or IP on save

The system SHALL refuse to save a device when its name or IP address matches another saved device, and SHALL report to the user which field collided without leaving the add/edit entry point. Name comparison MUST be case-insensitive and ignore leading and trailing whitespace; IP comparison MUST match exactly after ignoring leading and trailing whitespace. When both a name and an IP collision are present, the system SHALL report the name collision. When editing an existing device, that device MUST be excluded from the comparison so that re-saving it with an unchanged name or IP succeeds.

#### Scenario: Adding a device with a duplicate name

- **WHEN** the user adds a device whose name matches an existing device's name (ignoring case and surrounding whitespace)
- **THEN** the device is not saved
- **AND** the user is shown a message identifying the duplicate name and remains on the add screen

#### Scenario: Adding a device with a duplicate IP

- **WHEN** the user adds a device whose IP matches an existing device's IP
- **THEN** the device is not saved
- **AND** the user is shown a message identifying the duplicate IP and remains on the add screen

#### Scenario: Adding a device with a unique name and IP

- **WHEN** the user adds a device whose name and IP match no existing device
- **THEN** the device is saved and the entry point is dismissed

#### Scenario: Editing a device without changing its identity

- **WHEN** the user edits a device and saves it with its own name and IP unchanged
- **THEN** the device is saved successfully because it is excluded from the duplicate comparison

#### Scenario: Editing a device onto another device's name

- **WHEN** the user edits a device and changes its name to match a different saved device
- **THEN** the change is not saved
- **AND** the user is shown a message identifying the duplicate name and remains on the edit screen
