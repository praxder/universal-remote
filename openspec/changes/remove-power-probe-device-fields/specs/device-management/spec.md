## MODIFIED Requirements

### Requirement: Persistent device store
The system SHALL persist saved devices and their pairing credentials to a local file in the user's configuration directory. The file MUST be written with owner-only permissions (`0600`) because it contains secrets. Loading the store MUST tolerate entries that carry unknown legacy fields (such as `mac` and `model`) by ignoring them rather than failing.

#### Scenario: Store is created on first save
- **WHEN** a device is saved and no store file exists yet
- **THEN** the system creates the config directory and store file with mode `0600`
- **AND** the saved device is present when the store is read again

#### Scenario: Credentials round-trip
- **WHEN** a device with a pairing credential is saved and later loaded
- **THEN** the loaded device carries the same credential value

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

## REMOVED Requirements

### Requirement: Add device with IP auto-fill
**Reason**: The network probe and the model/MAC fields it auto-filled have been removed. Model was display-only and never used to connect; MAC fed only the now-removed Wake-on-LAN power-on. Adding a device is now manual IP + Name entry.
**Migration**: None. Existing saved devices are unaffected; the probe step is simply no longer offered.

## ADDED Requirements

### Requirement: Add device by manual entry
The system SHALL let a user add a device by manually entering an IP address and a name, with no network probe. The system SHALL let the user select which platform the device targets, defaulting to the first registered platform, and SHALL store the selected platform on the device.

#### Scenario: Device saved from manual entry
- **WHEN** the user enters an IP address and a name and saves
- **THEN** the system stores a device with those values and the selected platform

#### Scenario: Platform selected when adding a device
- **WHEN** the user adds a device
- **THEN** the system offers the registered platforms for selection, defaulting to the first
- **AND** the device is saved with the platform the user selected
