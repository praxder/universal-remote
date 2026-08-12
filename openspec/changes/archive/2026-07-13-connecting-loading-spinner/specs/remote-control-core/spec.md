## ADDED Requirements

### Requirement: Connect is bounded and reports failure distinctly
Connecting to a device SHALL complete or fail within a bounded time rather than blocking indefinitely on an unreachable device. When a connection cannot be established — the device is unreachable, refuses the connection, or does not respond within the bound — the adapter SHALL raise a distinct connection-failure error that callers can catch and present, rather than surfacing a raw transport error or hanging. A successful connect SHALL continue to return a session as before.

#### Scenario: Unreachable device fails within bounded time
- **WHEN** a caller connects to a device that does not respond
- **THEN** the connect attempt ends within a bounded timeout rather than blocking indefinitely
- **AND** it raises a distinct connection-failure error

#### Scenario: Connection refused reports failure
- **WHEN** a caller connects to a device that refuses the connection
- **THEN** the adapter raises the distinct connection-failure error rather than leaking a raw transport error

#### Scenario: Successful connect is unaffected
- **WHEN** a caller connects to a reachable device with a valid credential
- **THEN** the adapter returns a usable session as before
