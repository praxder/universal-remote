## ADDED Requirements

### Requirement: Fire TV adapter registration
The system SHALL provide an adapter for the Amazon Fire TV platform, registered under a stable platform identifier so devices of that platform resolve to it.

#### Scenario: Adapter is resolvable
- **WHEN** the registry is asked for the Fire TV platform identifier
- **THEN** it returns the Fire TV adapter

### Requirement: Declared Fire TV capabilities
The Fire TV adapter SHALL declare support for the directional keys, OK, back, home, menu, volume up, volume down, mute, the discrete play, pause, and stop keys, the combined play/pause key, rewind, fast-forward, and the number-pad digits. It SHALL NOT declare channel up or channel down, which a Fire TV streamer has no tuner to use. It SHALL declare its text support flag.

#### Scenario: Capabilities include the Fire TV button set
- **WHEN** the adapter's capabilities are read
- **THEN** the directional keys, OK, back, home, menu, volume up, volume down, mute, play, pause, play/pause, rewind, fast-forward, stop, and the number-pad digits are present
- **AND** no device connection is required to read them

#### Scenario: Channel keys are not declared
- **WHEN** the adapter's capabilities are read
- **THEN** the channel up and channel down keys are absent, so the on-screen remote disables them for Fire TV devices

### Requirement: Popup pairing yields a persistable credential
The Fire TV adapter SHALL require pairing and pair through a device-side authorization popup, without prompting the user for a value. Pairing SHALL produce an opaque credential that later connections replay so the authorization popup is not shown again.

#### Scenario: Adapter requires pairing
- **WHEN** the application checks whether the Fire TV adapter requires pairing before connecting
- **THEN** the adapter reports that it does

#### Scenario: Pairing returns a credential without prompting
- **WHEN** the adapter pairs with a device that accepts the authorization popup
- **THEN** the adapter returns an opaque credential to persist
- **AND** it does not request any value from the user during pairing

### Requirement: Connect replays the credential and verifies reachability
The Fire TV adapter SHALL establish a session to a device at its stored address using the stored credential, confirming the device is reachable before returning the session and reporting a failed connection when it is not.

#### Scenario: Reachable device yields a session
- **WHEN** the adapter connects to a reachable Fire TV at the stored address with a valid stored credential
- **THEN** it returns a session for sending keys and text

#### Scenario: Unreachable device reports connection failure
- **WHEN** the adapter connects and the device at the stored address is unreachable, refuses, times out, or rejects the credential
- **THEN** the adapter reports the connection as failed rather than returning a broken session

### Requirement: Key mapping
The Fire TV adapter SHALL translate each supported generic key into the corresponding Fire TV control action when sending over a session, so callers reference only generic keys.

#### Scenario: Supported key mapped
- **WHEN** a supported key is sent over a session
- **THEN** the adapter sends the matching Fire TV control action to the device

#### Scenario: Unsupported key rejected
- **WHEN** a caller sends a key the adapter does not declare
- **THEN** the session reports the key as unsupported and does not send an arbitrary substitute

### Requirement: Low-latency key dispatch with fallback
The Fire TV adapter SHALL prefer a faster device input path for keys that support it, and SHALL fall back to the standard key-event path for any other key or when the faster path is unavailable, without changing which action a key sends.

#### Scenario: Fast path used when available
- **WHEN** a key the faster input path supports is sent over a session to a device that exposes that path
- **THEN** the adapter dispatches it over the faster path
- **AND** the action sent is the one that key maps to

#### Scenario: Fallback preserves behaviour
- **WHEN** a key has no faster-path mapping, or the device exposes no faster path
- **THEN** the adapter dispatches it over the standard key-event path
- **AND** the key still sends its mapped action

### Requirement: Best-effort text entry
The Fire TV adapter SHALL attempt to send text to the device as literal characters, and SHALL report text as unsupported when the attempt fails, rather than silently discarding the text.

#### Scenario: Text unsupported reported
- **WHEN** a text send fails
- **THEN** the session reports text-unsupported so the caller can inform the user

### Requirement: Human-readable display name
The Fire TV adapter SHALL expose a human-readable display name, "Fire TV", distinct from its platform identifier, so the UI can present the platform without encoding brand knowledge.

#### Scenario: Display name exposed
- **WHEN** the adapter's display name is read
- **THEN** it is "Fire TV"
- **AND** the platform identifier remains "firetv"
