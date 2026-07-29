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
