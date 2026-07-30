## ADDED Requirements

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
The Fire TV adapter SHALL enter text by setting the contents of the device's focused text field, without requiring the caller to escape any character, and SHALL support characters outside the ASCII range. It SHALL report text as unsupported when no text field is focused, rather than reporting success for text the device discarded.

#### Scenario: Text entered into a focused field
- **WHEN** text is sent over a session while the device has a focused text field
- **THEN** the field contains that text

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

## MODIFIED Requirements

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

## REMOVED Requirements

### Requirement: Popup pairing yields a persistable credential
**Reason**: The remote-control API pairs by displaying a PIN on the television that the user types in; there is no device-side authorization popup to accept. The replacement is the "PIN pairing yields a persistable credential" requirement above.

**Migration**: Existing Fire TV devices hold an ADB RSA private key that the remote-control API does not accept. Those devices must be re-paired, which stores the new opaque token in its place.

### Requirement: Low-latency key dispatch with fallback
**Reason**: The faster path and its fallback both described dispatch through ADB shell commands against a device input node, which no longer exists once ADB is removed. The remote-control API has a single dispatch path, covered by the "Key dispatch over the remote HTTP API" requirement above, and is already faster than the path this requirement was written to optimise.

**Migration**: None required. Every key the fast path covered is dispatched by the replacement requirement, except the keys this change removes from the declared capability set.

### Requirement: Best-effort text entry
**Reason**: Text entry is no longer best-effort. The remote-control API sets the focused field's contents directly, needs no shell escaping, and reports whether a text field is focused, so success and failure are known rather than attempted. The replacement is the "Text entry through the device keyboard" requirement above.

**Migration**: None required. Callers continue to send text and to handle a text-unsupported report; the report is now accurate rather than inferred from a failed shell command.
