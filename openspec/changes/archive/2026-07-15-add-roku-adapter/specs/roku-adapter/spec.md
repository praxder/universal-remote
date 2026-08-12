## ADDED Requirements

### Requirement: Roku adapter registration
The system SHALL provide an adapter for the Roku platform, registered under a stable platform identifier so devices of that platform resolve to it.

#### Scenario: Adapter is resolvable
- **WHEN** the registry is asked for the Roku platform identifier
- **THEN** it returns the Roku adapter

### Requirement: Declared Roku capabilities
The Roku adapter SHALL declare support for the directional keys, OK, back, home, volume up, volume down, mute, channel up, channel down, the combined play/pause key, rewind, and fast-forward. It SHALL NOT declare discrete play, pause, or stop keys, the number-pad digits, or a menu key, none of which Roku's control protocol exposes. It SHALL declare its text support flag.

#### Scenario: Capabilities include the Roku button set
- **WHEN** the adapter's capabilities are read
- **THEN** the directional keys, OK, back, home, volume up, volume down, mute, channel up, channel down, play/pause, rewind, and fast-forward are present
- **AND** no device connection is required to read them

#### Scenario: Unsupported keys are not declared
- **WHEN** the adapter's capabilities are read
- **THEN** the discrete play, pause, and stop keys, the number-pad digits, and the menu key are absent, so the on-screen remote disables them for Roku devices

### Requirement: No pairing
The Roku adapter SHALL declare that it requires no pairing, because its control protocol is unauthenticated and issues no credential. The adapter SHALL NOT be asked to pair; if pairing is nonetheless attempted, it SHALL report pairing as unavailable rather than returning a credential.

#### Scenario: Adapter declares it needs no pairing
- **WHEN** the application checks whether the Roku adapter requires pairing before connecting
- **THEN** the adapter reports that it does not

#### Scenario: Pairing is unavailable
- **WHEN** the adapter is nonetheless asked to pair
- **THEN** it reports pairing as unavailable and returns no credential

### Requirement: Connect verifies reachability
The Roku adapter SHALL establish a session to a device at its stored address, confirming the device is reachable before returning the session and reporting a failed connection when it is not.

#### Scenario: Reachable device yields a session
- **WHEN** the adapter connects to a reachable Roku at the stored address
- **THEN** it returns a session for sending keys and text

#### Scenario: Unreachable device reports connection failure
- **WHEN** the adapter connects and the device at the stored address is unreachable, refuses, or times out
- **THEN** the adapter reports the connection as failed rather than returning a broken session

### Requirement: Key mapping
The Roku adapter SHALL translate each supported generic key into the corresponding Roku control-protocol key when sending over a session, so callers reference only generic keys.

#### Scenario: Supported key mapped
- **WHEN** a supported key is sent over a session
- **THEN** the adapter sends the matching Roku control-protocol key to the device

#### Scenario: Play/pause maps to the single toggle
- **WHEN** the combined play/pause key is sent over a session
- **THEN** the adapter sends Roku's single play/pause toggle

#### Scenario: Unsupported key rejected
- **WHEN** a caller sends a key the adapter does not declare
- **THEN** the session reports the key as unsupported and does not send an arbitrary substitute

### Requirement: Best-effort text entry
The Roku adapter SHALL attempt to send text to the device as literal characters, and SHALL report text as unsupported when the attempt fails, rather than silently discarding the text.

#### Scenario: Text unsupported reported
- **WHEN** a text send fails
- **THEN** the session reports text-unsupported so the caller can inform the user

### Requirement: Human-readable display name
The Roku adapter SHALL expose a human-readable display name, "Roku", distinct from its platform identifier, so the UI can present the platform without encoding brand knowledge.

#### Scenario: Display name exposed
- **WHEN** the adapter's display name is read
- **THEN** it is "Roku"
- **AND** the platform identifier remains "roku"
