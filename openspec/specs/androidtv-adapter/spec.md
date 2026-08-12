# androidtv-adapter Specification

## Purpose
Control Android TV / Google TV devices over the Remote v2 protocol — keys, pairing, and text alike, with no ADB — behind the generic remote-control seam.
## Requirements
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
The Android TV adapter SHALL send text to the device over the Remote v2 input-method path as literal characters, without requiring developer mode, ADB, or wireless debugging.

The adapter SHALL build each text edit from the device's most recently reported text-field state: the edit's field counter SHALL be the counter the device reports on that state and SHALL be re-read for every send rather than derived by incrementing a previous value, and the edit's cursor span SHALL be the position resulting from the send — the field's current contents plus the text being sent — so that consecutive sends append rather than overwrite.

The edit's input-method counter SHALL be the focused editor's own counter, which the device reports alongside the foreground application, rather than the counter the device carries on its inbound batch edit — that value is a fixed greeting rather than live state, and matches the editor's counter only on the device's own launcher. It SHALL likewise be re-read for every send, so moving to another application's text field does not reuse a stale value.

The adapter SHALL keep that state current by observing the device's own reports of its focused text field, which the device sends whenever the field changes from any source, including edits made with the physical remote.

The adapter SHALL NOT send the device's field-state report back to the device, because doing so causes the device to discard the input-method session.

When no text field is focused the device reports no field state, so the adapter SHALL report text as unsupported rather than sending an edit the device would silently discard. The adapter SHALL also report text as unsupported when a send otherwise fails, rather than silently discarding the text.

Because the device reports a text field gaining focus but never reports losing it, the adapter SHALL treat a send as delivered only once the device reports the resulting field state, and SHALL report text as unsupported when no such report arrives. Without that confirmation an edit built from state the device has since moved on from would be discarded in silence and reported to the user as a success.

#### Scenario: Text unsupported reported
- **WHEN** a text send fails
- **THEN** the session reports text-unsupported so the caller can inform the user

#### Scenario: Text is sent over Remote v2 with no ADB
- **WHEN** text is sent through a session to a device whose text field is focused
- **THEN** the adapter sends it over the Remote v2 input-method path
- **AND** it does not invoke `adb` or require developer mode or wireless debugging

#### Scenario: Field counter is taken from the latest reported state
- **WHEN** the device reports a new text-field state and text is then sent
- **THEN** the edit carries the field counter from that latest report
- **AND** the adapter does not increment a previously used counter to derive it

#### Scenario: Input-method counter is taken from the focused editor
- **WHEN** the device reports a focused editor whose counter differs from the one on its inbound batch edit, and text is then sent
- **THEN** the edit carries the focused editor's reported counter
- **AND** text sent into an application's own text field is accepted rather than silently discarded

#### Scenario: Consecutive sends append
- **WHEN** two text sends are made in succession to the same focused field
- **THEN** the second send's cursor span accounts for the text the first send added
- **AND** the field ends up containing both sends' text in order

#### Scenario: A discarded edit is reported rather than appearing to succeed
- **WHEN** text is sent and the device does not report the resulting field state
- **THEN** the session reports text-unsupported
- **AND** the caller is not told the text was delivered

#### Scenario: No focused text field reports text unsupported
- **WHEN** text is sent and the device has reported no focused text field
- **THEN** the session reports text-unsupported
- **AND** the adapter does not send an edit

### Requirement: Human-readable display name
The Android TV adapter SHALL expose a human-readable display name, "Android TV", distinct from its platform identifier, so the UI can present the platform without encoding brand knowledge.

#### Scenario: Display name exposed
- **WHEN** the adapter's display name is read
- **THEN** it is "Android TV"
- **AND** the platform identifier remains "androidtv"

