# firetv-adapter Specification

## Purpose
Control Amazon Fire TV devices — pairing with a PIN the device displays, and dispatching keys and text over the device's remote-control HTTP API — behind the generic remote-control seam.
## Requirements
### Requirement: Fire TV adapter registration
The system SHALL provide an adapter for the Amazon Fire TV platform, registered under a stable platform identifier so devices of that platform resolve to it.

#### Scenario: Adapter is resolvable
- **WHEN** the registry is asked for the Fire TV platform identifier
- **THEN** it returns the Fire TV adapter

### Requirement: Declared Fire TV capabilities
The Fire TV adapter SHALL declare support for the directional keys, OK, back, home, menu, the discrete play and pause keys, rewind, fast-forward, and the number-pad digits. It SHALL NOT declare channel up or channel down, which a Fire TV streamer has no tuner to use. It SHALL NOT declare volume up, volume down, or mute, which a Fire TV streamer reports it cannot control. It SHALL NOT declare the combined play/pause key or the stop key, for which the device offers no control action. It SHALL declare its text support flag.

#### Scenario: Capabilities include the Fire TV button set
- **WHEN** the adapter's capabilities are read
- **THEN** the directional keys, OK, back, home, menu, play, pause, rewind, fast-forward, and the number-pad digits are present
- **AND** no device connection is required to read them

#### Scenario: Channel keys are not declared
- **WHEN** the adapter's capabilities are read
- **THEN** the channel up and channel down keys are absent, so the on-screen remote disables them for Fire TV devices

#### Scenario: Volume keys are not declared
- **WHEN** the adapter's capabilities are read
- **THEN** the volume up, volume down, and mute keys are absent, so the on-screen remote disables them for Fire TV devices

#### Scenario: Combined play/pause and stop are not declared
- **WHEN** the adapter's capabilities are read
- **THEN** the combined play/pause key and the stop key are absent, so the on-screen remote disables them for Fire TV devices

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

### Requirement: Human-readable display name
The Fire TV adapter SHALL expose a human-readable display name, "Fire TV", distinct from its platform identifier, so the UI can present the platform without encoding brand knowledge.

#### Scenario: Display name exposed
- **WHEN** the adapter's display name is read
- **THEN** it is "Fire TV"
- **AND** the platform identifier remains "firetv"

### Requirement: Remote service wake before use
The Fire TV adapter SHALL start the device's remote-control service before pairing or connecting, because the service's control port is closed until it is started. The wake SHALL be idempotent, so waking an already-running service is harmless, and the adapter SHALL wait for the control port to accept connections before proceeding.

#### Scenario: Wake precedes pairing and connecting
- **WHEN** the adapter pairs with or connects to a Fire TV
- **THEN** it first starts the device's remote-control service
- **AND** it waits for the control port to become available before continuing

#### Scenario: Waking an already-running service is harmless
- **WHEN** the adapter wakes a device whose remote-control service is already running
- **THEN** the wake succeeds and the adapter proceeds normally

#### Scenario: Service that never becomes available fails the operation
- **WHEN** the control port does not accept connections within the adapter's timeout after a wake
- **THEN** the adapter reports the operation as failed rather than issuing commands against a closed port

### Requirement: PIN pairing yields a persistable credential
The Fire TV adapter SHALL require pairing, SHALL cause the device to display a PIN, and SHALL obtain that PIN from the user through the pairing prompt seam. Pairing SHALL produce an opaque credential that later connections replay so the PIN is not requested again. When no prompt is supplied, the adapter SHALL report pairing as failed rather than guessing a value.

#### Scenario: Adapter requires pairing
- **WHEN** the application checks whether the Fire TV adapter requires pairing before connecting
- **THEN** the adapter reports that it does

#### Scenario: Pairing displays a PIN and prompts for it
- **WHEN** the adapter pairs with a device
- **THEN** it asks the device to display a PIN
- **AND** it requests that PIN from the user through the pairing prompt
- **AND** it returns an opaque credential to persist once the PIN is accepted

#### Scenario: Rejected PIN reports pairing failure
- **WHEN** the user supplies a PIN the device does not accept
- **THEN** the adapter reports pairing as failed and returns no credential

#### Scenario: Missing prompt reports pairing failure
- **WHEN** pairing is attempted without a prompt seam
- **THEN** the adapter reports pairing as failed rather than supplying a value of its own

### Requirement: Key dispatch over the remote HTTP API
The Fire TV adapter SHALL dispatch keys as individual requests to the device's remote-control HTTP API, authenticated with the stored credential. It SHALL send each key in the request form the device answers with a truthful success or failure status, so an unsupported or rejected key is reported rather than assumed to have worked.

#### Scenario: Supported key dispatched and confirmed
- **WHEN** a declared key is sent over a session
- **THEN** the adapter issues the matching remote-control request
- **AND** a success status from the device is reported as success

#### Scenario: Rejected key reports failure
- **WHEN** the device rejects a key request
- **THEN** the adapter reports the failure rather than treating it as success

#### Scenario: Missing or invalid credential is rejected by the device
- **WHEN** a key request is made without a valid stored credential
- **THEN** the device rejects it and the adapter reports the failure

### Requirement: Text entry through the device keyboard
The Fire TV adapter SHALL enter text by setting the contents of the device's focused text field, without requiring the caller to escape any character, and SHALL support characters outside the ASCII range. It SHALL report text as unsupported when no text field is focused, rather than reporting success for text the device discarded. Because the device reports success for a write it discarded, the adapter SHALL confirm a send by reading the field's contents back, and SHALL NOT decide whether a field can be written to from the device's reported keyboard state alone.

#### Scenario: Text entered into a focused field
- **WHEN** text is sent over a session while the device has a focused text field
- **THEN** the field contains that text

#### Scenario: A field that has never been typed into still accepts text
- **WHEN** text is sent to a text field that holds focus but that nothing has yet been typed into, such as the device's search field immediately after it opens
- **THEN** the field contains that text
- **AND** the send is reported as successful

#### Scenario: Success is confirmed from the field, not the reply
- **WHEN** the device answers a text write with a success status but the field does not contain the text
- **THEN** the session reports text-unsupported rather than treating the status as success

#### Scenario: Characters needing no caller escaping
- **WHEN** text containing spaces, punctuation, or non-ASCII characters is sent
- **THEN** the field contains exactly the characters that were sent

#### Scenario: No focused field reports text unsupported
- **WHEN** text is sent while the device has no focused text field
- **THEN** the session reports text-unsupported so the caller can inform the user
- **AND** it does not report the send as successful

### Requirement: Reachability port open on a stock device
The Fire TV adapter SHALL declare a reachability port that a Fire TV answers in its stock configuration, without developer options enabled and without the remote-control service having been started, so a saved Fire TV is not reported unreachable merely because its control service is idle.

#### Scenario: Stock device reports reachable
- **WHEN** a saved Fire TV in its stock configuration is probed for reachability
- **THEN** the probe reports it reachable

#### Scenario: Idle remote service still reports reachable
- **WHEN** a saved Fire TV is probed before its remote-control service has been started
- **THEN** the probe reports it reachable
