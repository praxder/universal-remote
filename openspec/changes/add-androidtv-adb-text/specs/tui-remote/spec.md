## ADDED Requirements

### Requirement: Set up text input over ADB

The application SHALL provide a per-device action to set up text input over ADB for Android TV devices. The action SHALL guide the user to enable Developer options and Wireless debugging on the device and open its "Pair with code" screen, then collect the pairing address and the pairing code through prompts. It SHALL run the one-time ADB pairing through the adapter; on success it SHALL record the device as opted into ADB text and persist that opt-in; on failure it SHALL report the failure and leave the device unchanged.

#### Scenario: Successful setup records the opt-in

- **WHEN** the user completes the ADB text setup action with a valid pairing address and code and pairing succeeds
- **THEN** the application records the device as opted into ADB text, persists the change, and confirms setup to the user

#### Scenario: Failed setup leaves the device unchanged

- **WHEN** the user runs the ADB text setup action and pairing fails
- **THEN** the application reports the failure and does not mark the device as opted into ADB text

### Requirement: ADB text unavailable is surfaced during use

When a device is opted into ADB text and a text send falls back to Remote v2 because the ADB path was unavailable, the Use Remote surface SHALL show a one-line status explaining that ADB text was unavailable, rather than failing silently or blocking further use.

#### Scenario: Fallback shows a status message

- **WHEN** an opted-in device's text send falls back to Remote v2 because the ADB path was unavailable
- **THEN** the remote shows a one-line status explaining that ADB text was unavailable
