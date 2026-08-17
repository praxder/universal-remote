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
The Fire TV adapter SHALL enter text on a Fire TV whose properties do not report the
native platform type by setting the contents of its focused text field, without requiring
the caller to escape any character, and SHALL support characters outside the ASCII range.
It SHALL report text as unsupported when no text field is focused, rather than reporting
success for text the device discarded. Because the device reports success for a write it
discarded, the adapter SHALL confirm a send by reading the field's contents back, and
SHALL NOT decide whether a field can be written to from the device's reported keyboard
state alone. A Fire TV whose properties report the native platform type is covered by the
Vega text-entry requirement instead, and the adapter SHALL NOT apply this path to such a
device.

#### Scenario: Text entered into a focused field
- **WHEN** text is sent over a session to a device that is not the Vega platform, while the device has a focused text field
- **THEN** the field contains that text

#### Scenario: A field that has never been typed into still accepts text
- **WHEN** text is sent to a text field that holds focus but that nothing has yet been typed into, such as the device's search field immediately after it opens
- **THEN** the field contains that text
- **AND** the send is reported as successful

#### Scenario: Success is confirmed from the field, not the reply
- **WHEN** the device answers a text write with a success status but the field does not contain the text
- **THEN** the session reports text-unsupported rather than treating the status as success

#### Scenario: Characters needing no caller escaping
- **WHEN** text containing spaces, punctuation, or non-ASCII characters is sent to a device that is not the Vega platform
- **THEN** the field contains exactly the characters that were sent

#### Scenario: No focused field reports text unsupported
- **WHEN** text is sent while a device that is not the Vega platform has no focused text field
- **THEN** the session reports text-unsupported so the caller can inform the user
- **AND** it does not report the send as successful

#### Scenario: An absent field value reads as empty text
- **WHEN** the device answers a keyboard-state read with the field's contents reported as null rather than as a string
- **THEN** the adapter treats the contents as empty text
- **AND** no caller of the read fails with a type error

### Requirement: Reachability port open on a stock device
The Fire TV adapter SHALL declare a reachability port that a Fire TV answers in its stock configuration, without developer options enabled and without the remote-control service having been started, so a saved Fire TV is not reported unreachable merely because its control service is idle.

#### Scenario: Stock device reports reachable
- **WHEN** a saved Fire TV in its stock configuration is probed for reachability
- **THEN** the probe reports it reachable

#### Scenario: Idle remote service still reports reachable
- **WHEN** a saved Fire TV is probed before its remote-control service has been started
- **THEN** the probe reports it reachable

### Requirement: Fire TV platform detection at connect
The Fire TV adapter SHALL determine, once while connecting, whether a Fire TV runs the
Vega platform, so the session it returns holds the text path that device actually
answers. It SHALL read the device's properties route only when the device's own info
reports that route exists, and SHALL treat a reported native platform type as Vega.
Detection SHALL NOT be repeated per keypress, and a properties read that fails SHALL NOT
fail the connection — the session falls back to the keyboard text path, leaving every
key working on a device whose platform could not be established.

#### Scenario: Native platform type selects the Vega text path
- **WHEN** a device's info reports that the properties route exists and that route reports a native platform type
- **THEN** the session entered text through the Vega text path

#### Scenario: A device without the properties route keeps the keyboard path
- **WHEN** a device's info does not report the properties route
- **THEN** the adapter does not request properties
- **AND** the session enters text through the keyboard path

#### Scenario: A failed properties read still yields a session
- **WHEN** a device reports the properties route exists but the read of it fails
- **THEN** connecting still succeeds
- **AND** the session enters text through the keyboard path

### Requirement: Text entry on a Vega Fire TV
The Fire TV adapter SHALL enter text on a Vega by typing it one character at a time over
the device's single-character text route, which appends to the focused field. Because
that route appends, the adapter SHALL type each character at most once: it SHALL make
the remote service ready before the first character rather than re-waking mid-string,
and a failure part-way through a string SHALL be reported as a failure that says part of
the text may already have been typed. The adapter SHALL refuse the whole send, before
typing any character, when the text holds a character the route cannot accept, so a
refused send leaves the field untouched. Because a Vega reports neither which field has
focus nor what a field holds, the adapter SHALL NOT claim a confirmation it cannot
obtain, and SHALL NOT report text as unsupported on the basis of the keyboard state a
Vega reports.

#### Scenario: Text is typed one character at a time
- **WHEN** text is sent over a session to a Vega with a focused text field
- **THEN** the adapter issues one single-character request per character, in the order the characters were given
- **AND** the field contains the characters appended to whatever it already held

#### Scenario: Text the route cannot accept is refused before anything is typed
- **WHEN** text containing a character outside the accepted range is sent to a Vega
- **THEN** the session reports text-unsupported, naming the limitation
- **AND** no character of that text was typed

#### Scenario: A failure part-way through a string is reported as partial
- **WHEN** the device stops answering after some characters of a string have been typed
- **THEN** the session reports the send as failed
- **AND** the failure says part of the text may already have been typed
- **AND** no character is typed a second time

#### Scenario: A Vega send is not gated on the reported keyboard state
- **WHEN** text is sent to a Vega that reports its keyboard state as hidden and its field contents as absent
- **THEN** the send is attempted rather than refused as unsupported
- **AND** a send the device accepts is reported as successful without a read-back

### Requirement: Digit keys on a Vega Fire TV
The Fire TV adapter SHALL send a digit key to a Vega as one character over the
single-character text route, rather than by reading the focused field's contents and
writing them back with the digit appended. A Vega reports no field contents to read
back, so the read-modify-write path cannot serve it.

#### Scenario: A digit key is typed as a single character
- **WHEN** a digit key is sent over a session to a Vega
- **THEN** the adapter issues one single-character request for that digit
- **AND** it does not read the field's contents first

#### Scenario: A digit key on a device reporting no contents does not fail with a type error
- **WHEN** a digit key is sent to a device that reports its field contents as absent
- **THEN** the session either types the digit or reports a domain failure
- **AND** it does not raise a type error out of the adapter
