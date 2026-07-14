# device-management Specification

## Purpose
TBD - created by archiving change scaffold-samsung-remote. Update Purpose after archive.
## Requirements
### Requirement: Persistent device store
The system SHALL persist saved devices and their pairing credentials to a local file in the user's configuration directory. The file MUST be written with owner-only permissions (`0600`) because it contains secrets. A device MAY carry an optional adapter-specific reconnection identifier, and the store SHALL persist and reload that identifier alongside the credential when present. Loading the store MUST tolerate entries that carry unknown legacy fields (such as `mac` and `model`) by ignoring them rather than failing, and MUST tolerate entries that omit the reconnection identifier by treating it as absent.

#### Scenario: Store is created on first save
- **WHEN** a device is saved and no store file exists yet
- **THEN** the system creates the config directory and store file with mode `0600`
- **AND** the saved device is present when the store is read again

#### Scenario: Credentials round-trip
- **WHEN** a device with a pairing credential is saved and later loaded
- **THEN** the loaded device carries the same credential value

#### Scenario: Reconnection identifier round-trips
- **WHEN** a device with a reconnection identifier is saved and later loaded
- **THEN** the loaded device carries the same identifier value

#### Scenario: Missing identifier tolerated on load
- **WHEN** the store file contains a device entry with no reconnection identifier
- **THEN** the device loads successfully with its identifier treated as absent

#### Scenario: Legacy fields ignored on load
- **WHEN** the store file contains a device entry with legacy `mac` or `model` keys
- **THEN** the device loads successfully with those keys ignored
- **AND** the keys are absent when the device is next saved

### Requirement: List devices
The system SHALL return all saved devices, each exposing at least name, platform, and IP address.

#### Scenario: Empty store
- **WHEN** the store contains no devices
- **THEN** the system returns an empty list without error

#### Scenario: Multiple devices
- **WHEN** the store contains two or more devices
- **THEN** the system returns all of them

### Requirement: Edit device
The system SHALL let a user modify the stored fields of an existing device.

#### Scenario: Edit persists
- **WHEN** the user edits a device's name and saves
- **THEN** subsequent reads of the store return the updated name

### Requirement: Delete device
The system SHALL let a user remove a saved device from the store.

#### Scenario: Delete removes device
- **WHEN** the user deletes a device
- **THEN** that device is no longer returned when listing devices
- **AND** other devices remain unaffected

### Requirement: Add device by manual entry
The system SHALL let a user add a device by manually entering an IP address and a name, with no network probe. The system SHALL let the user select which platform the device targets, offering the registered platforms by their human-readable names and defaulting to the first registered platform. The system SHALL store the selected platform on the device as its platform identifier, not its human-readable name.

#### Scenario: Device saved from manual entry
- **WHEN** the user enters an IP address and a name and saves
- **THEN** the system stores a device with those values and the selected platform

#### Scenario: Platform selected when adding a device
- **WHEN** the user adds a device
- **THEN** the system offers the registered platforms for selection by their human-readable names, defaulting to the first
- **AND** the device is saved with the platform identifier for the selection the user made

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

