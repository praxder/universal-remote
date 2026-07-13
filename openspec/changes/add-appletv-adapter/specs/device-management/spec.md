## MODIFIED Requirements

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
