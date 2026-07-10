# device-management Specification

## Purpose
TBD - created by archiving change scaffold-samsung-remote. Update Purpose after archive.
## Requirements
### Requirement: Persistent device store
The system SHALL persist saved devices and their pairing credentials to a local file in the user's configuration directory. The file MUST be written with owner-only permissions (`0600`) because it contains secrets.

#### Scenario: Store is created on first save
- **WHEN** a device is saved and no store file exists yet
- **THEN** the system creates the config directory and store file with mode `0600`
- **AND** the saved device is present when the store is read again

#### Scenario: Credentials round-trip
- **WHEN** a device with a pairing credential is saved and later loaded
- **THEN** the loaded device carries the same credential value

### Requirement: List devices
The system SHALL return all saved devices, each exposing at least name, platform, IP address, and (if known) MAC address.

#### Scenario: Empty store
- **WHEN** the store contains no devices
- **THEN** the system returns an empty list without error

#### Scenario: Multiple devices
- **WHEN** the store contains two or more devices
- **THEN** the system returns all of them

### Requirement: Add device with IP auto-fill
The system SHALL let a user add a device by entering an IP address, and SHALL attempt to auto-fill the device name, model, and MAC by probing the device over the network. Probe failure MUST NOT block adding the device. When more than one adapter is registered, the system SHALL let the user select which platform the device targets, defaulting to the first registered platform, and SHALL store the selected platform on the device. When only one adapter is registered, the system SHALL assign that platform without prompting.

#### Scenario: Probe succeeds
- **WHEN** the user enters an IP for a reachable, supported TV
- **THEN** the system pre-fills name, model, and MAC from the probe result for the user to confirm or edit

#### Scenario: Probe fails
- **WHEN** the user enters an IP that cannot be probed
- **THEN** the system falls back to a fully manual entry form
- **AND** the device can still be saved with user-entered values

#### Scenario: Platform selected when multiple adapters registered
- **WHEN** more than one adapter is registered and the user adds a device
- **THEN** the system offers the registered platforms for selection, defaulting to the first
- **AND** the device is saved with the platform the user selected

#### Scenario: Platform assigned when a single adapter registered
- **WHEN** only one adapter is registered and the user adds a device
- **THEN** the system assigns that platform without prompting for a selection

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

