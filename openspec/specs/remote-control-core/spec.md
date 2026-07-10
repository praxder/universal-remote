# remote-control-core Specification

## Purpose
TBD - created by archiving change scaffold-samsung-remote. Update Purpose after archive.
## Requirements
### Requirement: Generic key vocabulary
The system SHALL define a platform-agnostic set of remote keys that all callers use, independent of any TV brand. The vocabulary MUST cover directional navigation (up, down, left, right), select/OK, back, home, volume up, volume down, and mute.

#### Scenario: Callers reference generic keys only
- **WHEN** the UI or store issues a remote action
- **THEN** it references a generic key value, never a brand-specific key code

### Requirement: Capability declaration
An adapter SHALL declare which keys it supports and whether it supports text entry. Callers MUST be able to read these capabilities without connecting to a device.

#### Scenario: Capabilities readable before connect
- **WHEN** a caller inspects an adapter's capabilities
- **THEN** the adapter reports its supported keys and its text support flag
- **AND** no device connection is required to read them

### Requirement: Adapter registry
The system SHALL resolve a device's platform identifier to a registered adapter. Registering a new adapter MUST NOT require changes to the UI or device store.

#### Scenario: Known platform resolves
- **WHEN** a device names a registered platform
- **THEN** the registry returns the matching adapter

#### Scenario: Unknown platform is rejected
- **WHEN** a device names a platform with no registered adapter
- **THEN** the registry reports that the platform is unsupported rather than failing silently

### Requirement: Pairing lifecycle distinct from connecting
The system SHALL model pairing as a step separate from connecting. Pairing MAY require human interaction (a TV popup or a PIN) and SHALL produce a reusable credential that the caller can persist. A prompt hook MUST be available so adapters that need a PIN can request it.

#### Scenario: Pairing yields a credential
- **WHEN** an adapter completes pairing with a device
- **THEN** it returns a credential value that can be stored and replayed on later connects

#### Scenario: Pairing can be cancelled
- **WHEN** the user cancels an in-progress pairing
- **THEN** the operation stops without persisting a credential and reports cancellation

### Requirement: Session send and lifecycle
Connecting to a device with a valid credential SHALL yield a session that can send keys and text and be closed. The session MUST only act on keys the adapter declares as supported.

#### Scenario: Send a supported key
- **WHEN** a caller sends a supported key over an open session
- **THEN** the session dispatches the corresponding action to the device

#### Scenario: Reject an unsupported key
- **WHEN** a caller sends a key the adapter does not declare
- **THEN** the session reports the key as unsupported and does not send an arbitrary substitute

#### Scenario: Close releases resources
- **WHEN** a session is closed
- **THEN** its underlying connection is released and further sends fail cleanly

