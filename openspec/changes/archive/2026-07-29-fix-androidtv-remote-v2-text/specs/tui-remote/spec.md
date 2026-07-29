## MODIFIED Requirements

### Requirement: Text entry via a modal
The remote's Text action SHALL open a text-entry modal rather than focusing a docked field. While the modal's input is focused, typed characters fill a buffer and Enter sends the buffered text as a single text action and closes the modal; Escape closes the modal without sending the buffered text and without sending the device's Back key. When text is unsupported by the active adapter, activating the Text action SHALL surface a clear message that text is not supported on this device and SHALL NOT open an editable input.

When a text send is attempted and reported as unsupported, the status SHALL carry the reason the adapter gave — such as that no text field is focused on the device — rather than stating only that text is not supported, because the device-specific reason is what tells the user what to do about it. When the adapter gives no reason, the status SHALL fall back to stating that text is not supported on this device, so a send never fails without an explanation.

#### Scenario: Compose then send
- **WHEN** the text-entry modal is open and the user types characters and presses Enter
- **THEN** the buffered text is sent to the device as a single text action and the modal closes

#### Scenario: Escape closes the modal, not Back
- **WHEN** the text-entry modal is open and the user presses Escape
- **THEN** the modal closes, no buffered text is sent, and no Back key is sent to the device

#### Scenario: Text unsupported surfaces a message
- **WHEN** the active adapter reports text as unsupported and the user activates the Text action
- **THEN** a message explains text is not supported on this device and no editable text input is opened

#### Scenario: A failed send explains why
- **WHEN** the user sends text and the adapter reports it unsupported with a reason, such as no text field being focused on the device
- **THEN** the status shows that reason rather than only that text is not supported

#### Scenario: A failed send with no reason still explains itself
- **WHEN** the user sends text and the adapter reports it unsupported without giving a reason
- **THEN** the status states that text is not supported on this device

## REMOVED Requirements

### Requirement: Android TV text-input mode toggle
**Reason**: The toggle chose between Remote v2 text and the ADB text path. The ADB path is withdrawn, so the toggle offers a single option and the pairing prompt behind it collects an address and code the application no longer uses.
**Migration**: None required. Android TV devices send text over Remote v2 with no configuration. The Add and Edit Device screens present the same fields as every other device type.

### Requirement: Post-add ADB text hint for Android TV
**Reason**: The hint pointed the user at the withdrawn text-input-mode toggle to work around text that failed in some surfaces. Text now works over Remote v2 on the surface that failed, so the hint would direct the user to a control that no longer exists.
**Migration**: None required. Adding a discovered Android TV device shows no extra hint, matching every other device type.

### Requirement: ADB text unavailable is surfaced during use
**Reason**: Reported that a send had fallen back from the withdrawn ADB path to Remote v2. With Remote v2 the only text path there is no fallback to report. The condition worth surfacing is now that no text field is focused, which the adapter reports as text-unsupported through the existing text-failure status.
**Migration**: None required. The remote surface continues to show a one-line status when a text send cannot be delivered; the wording no longer references ADB.
