# apple-tv-adapter Specification

## Purpose
Control Apple TV devices over the Companion protocol, pairing by an on-screen PIN, behind the generic remote-control seam.
## Requirements
### Requirement: Apple TV adapter registration
The system SHALL provide an adapter for the Apple TV platform, registered under a stable platform identifier so devices of that platform resolve to it.

#### Scenario: Adapter is resolvable
- **WHEN** the registry is asked for the Apple TV platform identifier
- **THEN** it returns the Apple TV adapter

### Requirement: Declared Apple TV capabilities
The Apple TV adapter SHALL declare support for the directional keys, OK, back, home, volume up, and volume down. It SHALL NOT declare mute, which has no Apple TV equivalent. It SHALL declare its text support flag.

#### Scenario: Capabilities include the core button set
- **WHEN** the adapter's capabilities are read
- **THEN** the directional keys, OK, back, home, volume up, and volume down are present
- **AND** no device connection is required to read them

#### Scenario: Mute is not offered
- **WHEN** the adapter's capabilities are read
- **THEN** mute is absent, so the on-screen remote disables it for Apple TV devices

### Requirement: PIN pairing
The Apple TV adapter SHALL pair over the Companion protocol by beginning pairing so the Apple TV displays a PIN, requesting that PIN from the caller through the pairing prompt, submitting it, and returning the resulting credential for persistence. When no prompt is available, the adapter SHALL report pairing as cancelled rather than proceeding. Later connections SHALL reuse the stored credential without re-pairing.

#### Scenario: PIN pairing obtains a credential
- **WHEN** the adapter pairs with an Apple TV and the user enters the PIN shown on screen when prompted
- **THEN** the adapter submits the PIN and returns a credential that can be stored

#### Scenario: Pairing without a prompt is cancelled
- **WHEN** the adapter is asked to pair but no prompt is available to request the PIN
- **THEN** the adapter reports pairing as cancelled and returns no credential

#### Scenario: Stored credential reused
- **WHEN** the adapter connects with a previously stored credential
- **THEN** it establishes a session without pairing again

### Requirement: Reconnection identity
The Apple TV adapter SHALL record the device's platform identifier during pairing so it can be persisted, and SHALL verify at connect time that the device reachable at the stored address still matches that identifier before connecting.

#### Scenario: Identifier recorded at pairing
- **WHEN** the adapter completes pairing with an Apple TV
- **THEN** it records the Apple TV's identifier on the device for persistence

#### Scenario: Connect verifies identity
- **WHEN** the adapter connects and the device at the stored address does not match the stored identifier
- **THEN** the adapter reports the connection as failed rather than connecting to the wrong device

### Requirement: Key mapping
The Apple TV adapter SHALL translate each supported generic key into the corresponding Apple TV remote-control action when sending over a session, so callers reference only generic keys.

#### Scenario: Directional key mapped
- **WHEN** a supported directional or select key is sent
- **THEN** the adapter sends the matching Apple TV remote-control action to the device

#### Scenario: Back and home mapped
- **WHEN** the back or home key is sent over a session
- **THEN** the adapter sends the menu or home action respectively

#### Scenario: Volume keys are fire-and-forget
- **WHEN** volume up or volume down is sent over a session
- **THEN** the adapter presses the corresponding remote-control volume key without waiting for a volume-state acknowledgement
- **AND** an Apple TV that never reports its volume does not cause the send to time out or crash the remote

#### Scenario: Unsupported key rejected
- **WHEN** a caller sends a key the adapter does not declare
- **THEN** the session reports the key as unsupported and does not send an arbitrary substitute

### Requirement: Best-effort text entry
The Apple TV adapter SHALL attempt to send text to the device, and SHALL report text as unsupported when the attempt fails, rather than silently discarding the text.

#### Scenario: Text unsupported reported
- **WHEN** a text send fails
- **THEN** the session reports text-unsupported so the caller can inform the user

### Requirement: Human-readable display name
The Apple TV adapter SHALL expose a human-readable display name, "Apple TV", distinct from its platform identifier, so the UI can present the platform without encoding brand knowledge.

#### Scenario: Display name exposed
- **WHEN** the adapter's display name is read
- **THEN** it is "Apple TV"
- **AND** the platform identifier remains "apple-tv"
