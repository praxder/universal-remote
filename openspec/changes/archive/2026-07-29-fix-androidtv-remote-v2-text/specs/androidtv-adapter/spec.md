## MODIFIED Requirements

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

## REMOVED Requirements

### Requirement: Opt-in ADB text routing
**Reason**: The workaround this existed for is no longer needed — text now lands over Remote v2 on the surface that previously discarded it, so routing text over `adb` bought nothing while requiring developer mode and wireless debugging and conflicting with other `adb` use such as sideloading.
**Migration**: None required. Text for every Android TV device is sent over Remote v2, which is what the not-opted-in path already did. Devices previously opted in need no user action, and the ADB pairing they performed is simply no longer used rather than revoked.

### Requirement: ADB target resolution via mDNS
**Reason**: Existed only to find the ephemeral wireless-debugging port for the removed ADB text path.
**Migration**: None required. Remote v2 uses the device's stored address and its own fixed port.

### Requirement: ADB text fallback when unavailable
**Reason**: Existed only to recover when the removed ADB text path could not be reached. With text sent over Remote v2 there is no second path to fall back from, and the meaningful failure is now "no text field is focused", covered by the text-entry requirement.
**Migration**: None required. The remote surface reports text-unsupported instead of an ADB-unavailable status.

### Requirement: One-time ADB wireless-debugging pairing
**Reason**: Established trust used only by the removed ADB text path. Remote v2 PIN pairing, which is unaffected, is the adapter's only remaining pairing.
**Migration**: None required. Any ADB pairing already performed on a device is left in place and unused; the application no longer offers or needs it.
