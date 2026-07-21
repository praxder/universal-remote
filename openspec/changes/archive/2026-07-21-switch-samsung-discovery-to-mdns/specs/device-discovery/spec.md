## MODIFIED Requirements

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
