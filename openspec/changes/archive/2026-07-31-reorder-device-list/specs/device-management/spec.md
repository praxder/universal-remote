## ADDED Requirements

### Requirement: Reorder saved devices

The system SHALL let a user change the position of a saved device within the device list by moving it one place earlier or one place later, and SHALL persist the resulting order so it is the same on the next run. A move SHALL exchange the device with its immediate neighbour and SHALL NOT change any stored field of any device, including its name, platform, IP address, credential, and identifier. A move that has no neighbour to exchange with — moving the first device earlier or the last device later — SHALL leave the stored order unchanged, as SHALL a move naming a device that is not present in the store.

#### Scenario: Move a device earlier

- **WHEN** the second saved device is moved one place earlier
- **THEN** it is listed first and the previously first device is listed second
- **AND** the remaining devices keep their positions

#### Scenario: Move a device later

- **WHEN** the first saved device is moved one place later
- **THEN** it is listed second and the previously second device is listed first
- **AND** the remaining devices keep their positions

#### Scenario: Reordered order survives a reload

- **WHEN** a device is moved and the store is read again from disk
- **THEN** the devices are returned in the moved order

#### Scenario: Moving the first device earlier does nothing

- **WHEN** the first saved device is moved one place earlier
- **THEN** the stored order is unchanged

#### Scenario: Moving the last device later does nothing

- **WHEN** the last saved device is moved one place later
- **THEN** the stored order is unchanged

#### Scenario: Moving an unknown device does nothing

- **WHEN** a move names a device identifier that is not in the store
- **THEN** the stored order is unchanged

#### Scenario: A move preserves device fields

- **WHEN** a device carrying a pairing credential is moved
- **THEN** the moved device still carries the same name, platform, IP address, credential, and identifier

## MODIFIED Requirements

### Requirement: List devices
The system SHALL return all saved devices, each exposing at least name, platform, and IP address. The devices SHALL be returned in their stored order — the order the user has arranged them in (see the "Reorder saved devices" requirement) — and that order SHALL be stable across runs. Adding, editing, or deleting a device SHALL NOT reorder the devices that remain: a new device is appended last, an edited device keeps its position, and deleting a device leaves the relative order of the others intact.

#### Scenario: Empty store
- **WHEN** the store contains no devices
- **THEN** the system returns an empty list without error

#### Scenario: Multiple devices
- **WHEN** the store contains two or more devices
- **THEN** the system returns all of them

#### Scenario: Stored order is preserved on load
- **WHEN** a store holding several devices is read
- **THEN** the devices are returned in the same order they were stored in

#### Scenario: Adding a device appends it last
- **WHEN** a device is added to a store that already holds devices
- **THEN** the new device is returned last and the existing devices keep their order

#### Scenario: Deleting a device preserves the order of the rest
- **WHEN** a device is deleted from a store holding three or more devices
- **THEN** the remaining devices are returned in their previous relative order
