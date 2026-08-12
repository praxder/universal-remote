## MODIFIED Requirements

### Requirement: Add device with IP auto-fill
The system SHALL let a user add a device by entering an IP address, and SHALL attempt to auto-fill the device name, model, and MAC by probing the device over the network. Probe failure MUST NOT block adding the device. When more than one adapter is registered, the system SHALL let the user select which platform the device targets, defaulting to the first registered platform, and SHALL store the selected platform on the device. When only one adapter is registered, the system SHALL assign that platform without prompting.

#### Scenario: Probe succeeds
- **WHEN** the user enters an IP for a reachable, supported TV
- **THEN** the system pre-fills name, model, and MAC from the probe result for the user to confirm or edit

#### Scenario: Probe fails
- **WHEN** the user enters an IP that cannot be probed
- **THEN** the system falls back to a fully manual entry form
- **AND** the device can still be saved with user-entered values

#### Scenario: Platform selected when multiple adapters registered
- **WHEN** more than one adapter is registered and the user adds a device
- **THEN** the system offers the registered platforms for selection, defaulting to the first
- **AND** the device is saved with the platform the user selected

#### Scenario: Platform assigned when a single adapter registered
- **WHEN** only one adapter is registered and the user adds a device
- **THEN** the system assigns that platform without prompting for a selection
