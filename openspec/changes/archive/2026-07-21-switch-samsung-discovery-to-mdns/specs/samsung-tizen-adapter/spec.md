## ADDED Requirements

### Requirement: Network discovery of Samsung TVs

The Samsung Tizen adapter SHALL discover Samsung TVs on the local network by browsing the mDNS `_airplay._tcp` service, and SHALL report only responders whose advertised AirPlay metadata identifies the manufacturer as Samsung. Each reported device SHALL carry the Samsung Tizen platform identifier, its IP address, and its friendly name, falling back to the IP address when no usable friendly name is advertised. A responder that is not a Samsung device SHALL NOT be reported by this adapter, even though other vendors answer the same `_airplay._tcp` service.

#### Scenario: A Samsung TV is discovered

- **WHEN** a Samsung TV answering `_airplay._tcp` advertises its manufacturer as Samsung
- **THEN** the adapter reports it under the Samsung Tizen platform with its friendly name and IP address

#### Scenario: A non-Samsung AirPlay device is ignored

- **WHEN** a non-Samsung device (such as an Apple TV or an LG TV) answers the same `_airplay._tcp` browse
- **THEN** the adapter does not report it as a Samsung device

#### Scenario: Name falls back to IP

- **WHEN** a discovered Samsung TV advertises no usable friendly name
- **THEN** the reported name is the TV's IP address
