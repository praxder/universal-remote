## MODIFIED Requirements

### Requirement: Generic key vocabulary
The system SHALL define a platform-agnostic set of remote keys that all callers use, independent of any TV brand. The vocabulary MUST cover directional navigation (up, down, left, right), select/OK, back, home, volume up, volume down, and mute.

#### Scenario: Callers reference generic keys only
- **WHEN** the UI or store issues a remote action
- **THEN** it references a generic key value, never a brand-specific key code

### Requirement: Capability declaration
An adapter SHALL declare which keys it supports and whether it supports text entry. Callers MUST be able to read these capabilities without connecting to a device.

#### Scenario: Capabilities readable before connect
- **WHEN** a caller inspects an adapter's capabilities
- **THEN** the adapter reports its supported keys and its text support flag
- **AND** no device connection is required to read them
