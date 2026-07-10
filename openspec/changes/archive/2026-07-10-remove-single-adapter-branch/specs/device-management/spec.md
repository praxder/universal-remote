## MODIFIED Requirements

### Requirement: Add device with IP auto-fill
The system SHALL let a user add a device by entering an IP address, and SHALL attempt to auto-fill the device name, model, and MAC by probing the device over the network. Probe failure MUST NOT block adding the device. The system SHALL let the user select which platform the device targets, defaulting to the first registered platform, and SHALL store the selected platform on the device.

#### Scenario: Probe succeeds
- **WHEN** the user enters an IP for a reachable, supported TV
- **THEN** the system pre-fills name, model, and MAC from the probe result for the user to confirm or edit

#### Scenario: Probe fails
- **WHEN** the user enters an IP that cannot be probed
- **THEN** the system falls back to a fully manual entry form
- **AND** the device can still be saved with user-entered values

#### Scenario: Platform selected when adding a device
- **WHEN** the user adds a device
- **THEN** the system offers the registered platforms for selection, defaulting to the first
- **AND** the device is saved with the platform the user selected
