## ADDED Requirements

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
The system SHALL let a user add a device by entering an IP address, and SHALL attempt to auto-fill the device name, model, and MAC by probing the device over the network. Probe failure MUST NOT block adding the device.

#### Scenario: Probe succeeds
- **WHEN** the user enters an IP for a reachable, supported TV
- **THEN** the system pre-fills name, model, and MAC from the probe result for the user to confirm or edit

#### Scenario: Probe fails
- **WHEN** the user enters an IP that cannot be probed
- **THEN** the system falls back to a fully manual entry form
- **AND** the device can still be saved with user-entered values

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
