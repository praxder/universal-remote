## ADDED Requirements

### Requirement: Android TV adapter registration
The system SHALL provide an adapter for the Android TV / Google TV platform, registered under a stable platform identifier so devices of that platform resolve to it.

#### Scenario: Adapter is resolvable
- **WHEN** the registry is asked for the Android TV platform identifier
- **THEN** it returns the Android TV adapter

### Requirement: Declared Android TV capabilities
The Android TV adapter SHALL declare support for the directional keys, OK, back, home, menu, volume up, volume down, mute, channel up, channel down, the discrete play, pause, and stop keys, the combined play/pause key, rewind, fast-forward, and the number-pad digits. It SHALL declare its text support flag.

#### Scenario: Capabilities include the Android TV button set
- **WHEN** the adapter's capabilities are read
- **THEN** the directional keys, OK, back, home, menu, volume up, volume down, mute, channel up, channel down, play, pause, play/pause, stop, rewind, fast-forward, and the number-pad digits are present
- **AND** no device connection is required to read them

#### Scenario: Channel keys are declared
- **WHEN** the adapter's capabilities are read
- **THEN** the channel up and channel down keys are present, so the on-screen remote enables them for Android TV devices whose focused app consumes them

### Requirement: PIN pairing yields a persistable credential
The Android TV adapter SHALL require pairing and pair through a code the device displays, requesting that code through the pairing prompt hook. Pairing SHALL produce an opaque credential that later connections replay so the device does not prompt for a code again. When no prompt is available the adapter SHALL report pairing as cancelled rather than proceeding.

#### Scenario: Adapter requires pairing
- **WHEN** the application checks whether the Android TV adapter requires pairing before connecting
- **THEN** the adapter reports that it does

#### Scenario: Pairing requests the code and returns a credential
- **WHEN** the adapter pairs with a device that displays a pairing code and the prompt supplies that code
- **THEN** the adapter completes pairing and returns an opaque credential to persist

#### Scenario: Pairing without a prompt is cancelled
- **WHEN** the adapter is asked to pair with no prompt available
- **THEN** it reports pairing as cancelled and does not contact the device for a code

### Requirement: Connect replays the credential and verifies reachability
The Android TV adapter SHALL establish a session to a device at its stored address using the stored credential, confirming the device is reachable before returning the session and reporting a failed connection when it is not.

#### Scenario: Reachable device yields a session
- **WHEN** the adapter connects to a reachable Android TV at the stored address with a valid stored credential
- **THEN** it returns a session for sending keys and text

#### Scenario: Unreachable or unauthorized device reports connection failure
- **WHEN** the adapter connects and the device at the stored address is unreachable, refuses, times out, or rejects the credential
- **THEN** the adapter reports the connection as failed rather than returning a broken session

### Requirement: Key mapping
The Android TV adapter SHALL translate each supported generic key into the corresponding Android TV control action when sending over a session, so callers reference only generic keys.

#### Scenario: Supported key mapped
- **WHEN** a supported key is sent over a session
- **THEN** the adapter sends the matching Android TV control action to the device

#### Scenario: Unsupported key rejected
- **WHEN** a caller sends a key the adapter does not declare
- **THEN** the session reports the key as unsupported and does not send an arbitrary substitute

### Requirement: Best-effort text entry
The Android TV adapter SHALL attempt to send text to the device as literal characters, and SHALL report text as unsupported when the attempt fails, rather than silently discarding the text.

#### Scenario: Text unsupported reported
- **WHEN** a text send fails
- **THEN** the session reports text-unsupported so the caller can inform the user

### Requirement: Human-readable display name
The Android TV adapter SHALL expose a human-readable display name, "Android TV", distinct from its platform identifier, so the UI can present the platform without encoding brand knowledge.

#### Scenario: Display name exposed
- **WHEN** the adapter's display name is read
- **THEN** it is "Android TV"
- **AND** the platform identifier remains "androidtv"
