## ADDED Requirements

### Requirement: Android TV text-input mode toggle

The Add Device and Edit Device screens SHALL present a text-input-mode toggle **only when the device's type is Android TV**; for every other device type the toggle SHALL NOT appear, and the device list SHALL NOT offer any action to change a device's text-input mode. The toggle selects between standard Remote v2 text and ADB text.

When the user switches the toggle to ADB, the application SHALL run the one-time ADB pairing, prompting for the pairing address and pairing code and pairing through the adapter. On success the device SHALL be recorded as opted into ADB text when the form is saved. On cancel or failure the toggle SHALL revert to standard and the device SHALL NOT be opted in. Switching the toggle back to standard SHALL clear the opt-in without pairing.

#### Scenario: Toggle appears only for Android TV

- **WHEN** the Add or Edit screen is shown for an Android TV device
- **THEN** the text-input-mode toggle is visible
- **AND WHEN** the screen is shown for a device of any other type
- **THEN** the toggle is not shown

#### Scenario: Switching to ADB pairs and opts in on save

- **WHEN** the user switches the toggle to ADB, completes pairing with a valid address and code, and saves the form
- **THEN** the application records the device as opted into ADB text and persists it

#### Scenario: Failed or cancelled pairing reverts the toggle

- **WHEN** the user switches the toggle to ADB but the pairing is cancelled or fails
- **THEN** the toggle reverts to standard and the device is not opted into ADB text

#### Scenario: Editing flips an existing device's mode

- **WHEN** the user edits an Android TV device already opted into ADB text and switches the toggle back to standard, then saves
- **THEN** the device is no longer opted into ADB text and no pairing is run

### Requirement: Post-add ADB text hint for Android TV

When an Android TV device is added directly from the discovery screen, the application SHALL show a one-time hint that text input can be routed over ADB if it has trouble in some apps, pointing the user to edit the device and switch its text-input mode. The hint SHALL NOT appear when a device of any other type is added.

#### Scenario: Adding a discovered Android TV device shows the hint

- **WHEN** the user selects and adds an Android TV device from the discovery screen
- **THEN** the application shows a hint that text input can be switched to ADB, which the user dismisses

#### Scenario: Adding a non-Android device shows no hint

- **WHEN** the user selects and adds a device of any other type from the discovery screen
- **THEN** no ADB text hint is shown

### Requirement: ADB text unavailable is surfaced during use

When a device is opted into ADB text and a text send falls back to Remote v2 because the ADB path was unavailable, the Use Remote surface SHALL show a one-line status explaining that ADB text was unavailable, rather than failing silently or blocking further use.

#### Scenario: Fallback shows a status message

- **WHEN** an opted-in device's text send falls back to Remote v2 because the ADB path was unavailable
- **THEN** the remote shows a one-line status explaining that ADB text was unavailable
