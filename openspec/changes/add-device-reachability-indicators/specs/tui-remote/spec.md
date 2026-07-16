## ADDED Requirements

### Requirement: Reachability indicator in the Use Remote picker
The Use Remote device picker SHALL display a reachability indicator next to each saved device, positioned before the device's 1-based position number: green when the device is reachable, red when unreachable, and yellow when the status is unknown or has not yet been determined. The picker SHALL show every device immediately with a yellow (unknown) indicator, then determine each device's reachability without blocking selection, updating each indicator in place as its status resolves. The picker SHALL refresh reachability on a recurring interval while it is open and SHALL stop probing when the user leaves the screen. The indicator SHALL be advisory only: the user MAY select and connect to any device regardless of its indicator, including one shown as unreachable.

#### Scenario: Devices shown immediately as unknown
- **WHEN** the user opens Use Remote with one or more saved devices
- **THEN** each device is listed right away with a yellow indicator before its position number
- **AND** the list is usable before any reachability result has resolved

#### Scenario: Reachable device turns green
- **WHEN** a device's reachability resolves to reachable
- **THEN** that device's indicator updates in place to green

#### Scenario: Unreachable device turns red
- **WHEN** a device's reachability resolves to unreachable
- **THEN** that device's indicator updates in place to red

#### Scenario: Indicators refresh on an interval
- **WHEN** the picker has been open for the refresh interval
- **THEN** the picker re-probes the devices and updates each indicator to its current status

#### Scenario: Probing stops on leaving the screen
- **WHEN** the user leaves the Use Remote picker
- **THEN** no further reachability probes are started

#### Scenario: Unreachable device remains selectable
- **WHEN** a device shown with a red indicator is selected
- **THEN** the application begins the connect/pair flow for it exactly as for any other device
