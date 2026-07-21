# device-discovery Specification

## Purpose
TBD - created by syncing change add-device-discovery. Update Purpose after archive.
## Requirements
### Requirement: Discover devices across supported platforms
The system SHALL discover devices on the local network for every supported platform that can be discovered, reporting each discovered device with a name, a platform identifier resolvable by the adapter registry, and an IP address. Each platform's scan SHALL run concurrently, and discovery SHALL complete within a bounded time window. When a discovered device announces no usable friendly name, the reported name SHALL fall back to its IP address.

#### Scenario: A supported device is reported
- **WHEN** a supported device is announcing itself on the network
- **THEN** discovery reports it with its name, its platform identifier, and its IP address

#### Scenario: Name falls back to IP when unavailable
- **WHEN** a device is discovered but announces no usable friendly name
- **THEN** the reported name is the device's IP address

#### Scenario: Scans run concurrently within a bounded window
- **WHEN** discovery runs across multiple platforms
- **THEN** the platform scans run concurrently and discovery returns within a bounded time window

### Requirement: Discovery is best-effort
The system SHALL treat discovery as best-effort. A platform that is not discoverable, is unreachable, or whose scan fails or times out SHALL contribute no results, SHALL NOT raise an error to the user, and SHALL NOT abort discovery of the other platforms.

#### Scenario: Non-discoverable platform contributes nothing
- **WHEN** an adapter provides no discovery capability
- **THEN** it yields no discovered devices and discovery of the other platforms proceeds

#### Scenario: A failing scan is isolated
- **WHEN** one platform's scan fails or times out
- **THEN** the other platforms' discovered devices are still reported
- **AND** no error is surfaced to the user

### Requirement: Resolve multi-protocol collisions by fixed platform priority
When one device is discovered under more than one platform — identified by a shared IP address — the system SHALL report it exactly once, keeping the highest-priority platform. The priority order SHALL rank Fire TV above Android TV. Platforms that use a distinct, vendor-specific discovery target (the SSDP-based platforms, each with its own vendor target) do not cross-claim. Where platforms share a discovery service, each such platform's adapter SHALL restrict its reported devices to that platform: the Samsung Tizen adapter browses the shared `_airplay._tcp` mDNS service and SHALL report only responders whose AirPlay metadata identifies the manufacturer as Samsung, and the Apple TV scan — which AirPlay 2 makes answer for many third-party TVs (LG, Samsung) — SHALL report only devices that expose the Companion protocol it pairs and controls over. Together these adapter-level filters keep an AirPlay-capable TV from being reported under the wrong platform.

#### Scenario: Fire TV wins over Android TV
- **WHEN** a single IP address is discovered as both a Fire TV and an Android TV
- **THEN** a single entry is reported for that IP with the Fire TV platform

#### Scenario: An AirPlay-only TV is not reported as an Apple TV
- **WHEN** a non-Apple TV that supports AirPlay 2 but not the Companion protocol answers the Apple TV scan
- **THEN** it is not reported as an Apple TV, leaving its own platform's scan to report it under the correct platform

#### Scenario: A non-Samsung AirPlay TV is not reported as Samsung
- **WHEN** a non-Samsung TV that answers the `_airplay._tcp` mDNS browse does not identify its manufacturer as Samsung
- **THEN** it is not reported under the Samsung Tizen platform, leaving its own platform's scan to report it under the correct platform

#### Scenario: Distinct devices are both reported
- **WHEN** two different IP addresses are discovered
- **THEN** both devices are reported

### Requirement: Exclude already-saved devices
The system SHALL exclude from the discovery results any device whose IP address already belongs to a saved device in the store, comparing IP addresses exactly after trimming surrounding whitespace.

#### Scenario: A saved device is omitted
- **WHEN** a discovered device's IP address matches the IP address of a saved device
- **THEN** that device is not included in the discovery results

#### Scenario: A new device is included
- **WHEN** a discovered device's IP address matches no saved device
- **THEN** that device is included in the discovery results

