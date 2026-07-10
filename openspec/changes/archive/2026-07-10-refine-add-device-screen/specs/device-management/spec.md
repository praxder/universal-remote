## MODIFIED Requirements

### Requirement: Add device by manual entry
The system SHALL let a user add a device by manually entering an IP address and a name, with no network probe. The system SHALL let the user select which platform the device targets, offering the registered platforms by their human-readable names and defaulting to the first registered platform. The system SHALL store the selected platform on the device as its platform identifier, not its human-readable name.

#### Scenario: Device saved from manual entry
- **WHEN** the user enters an IP address and a name and saves
- **THEN** the system stores a device with those values and the selected platform

#### Scenario: Platform selected when adding a device
- **WHEN** the user adds a device
- **THEN** the system offers the registered platforms for selection by their human-readable names, defaulting to the first
- **AND** the device is saved with the platform identifier for the selection the user made
