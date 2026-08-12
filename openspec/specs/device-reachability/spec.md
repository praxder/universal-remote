# device-reachability Specification

## Purpose
Report a saved device's network reachability with a non-invasive, bounded TCP probe of its adapter's declared control port, without pairing, connecting, or any device side effect.
## Requirements
### Requirement: Reachability status model
The system SHALL represent a saved device's network reachability as exactly one of three states: reachable, unreachable, or unknown. The state SHALL be derivable for any saved device without the user having connected to it.

#### Scenario: Three distinct states
- **WHEN** a caller inspects a device's reachability
- **THEN** the result is one of reachable, unreachable, or unknown

### Requirement: Non-invasive TCP probe
The system SHALL determine reachability by attempting a TCP connection to the device's declared control port and MUST NOT pair, MUST NOT use or require a stored credential, MUST NOT open a control session, and MUST NOT cause any side effect on the device. A connection that succeeds within the timeout SHALL yield reachable; a refused connection, a timeout, or a network error SHALL yield unreachable.

#### Scenario: Open control port reports reachable
- **WHEN** the device's control port accepts a TCP connection within the timeout
- **THEN** the probe reports the device reachable

#### Scenario: Refused or unresponsive port reports unreachable
- **WHEN** the connection is refused, times out, or fails with a network error
- **THEN** the probe reports the device unreachable

#### Scenario: Probe does not connect or pair
- **WHEN** a device is probed for reachability
- **THEN** no pairing is performed, no credential is required, and no control session is opened

### Requirement: Per-adapter reachability port
Each platform adapter SHALL declare the TCP port used to probe its reachability, and that port SHALL be readable without connecting to a device. When an adapter declares no reachability port, a device on that platform SHALL have unknown reachability.

#### Scenario: Adapter declares a probe port
- **WHEN** a device's platform adapter declares a reachability port
- **THEN** the system probes that port to determine the device's reachability

#### Scenario: Adapter without a probe port yields unknown
- **WHEN** a device's platform adapter declares no reachability port
- **THEN** the device's reachability is reported as unknown and no probe is attempted

### Requirement: Bounded probe timeout
Reachability probing SHALL be bounded by a timeout so that an unreachable or slow-to-respond device resolves to unreachable within a fixed time rather than blocking indefinitely.

#### Scenario: Slow device resolves at the timeout
- **WHEN** a device neither accepts nor refuses the connection within the timeout
- **THEN** the probe reports the device unreachable once the timeout elapses
