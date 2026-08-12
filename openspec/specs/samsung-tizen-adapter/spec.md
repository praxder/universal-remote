# samsung-tizen-adapter Specification

## Purpose
Control Samsung Tizen TVs — pairing by a token from the TV's popup and discovering them via the AirPlay mDNS service — behind the generic remote-control seam.
## Requirements
### Requirement: Samsung Tizen adapter registration
The system SHALL provide an adapter for the Samsung Tizen platform, registered under a stable platform identifier so devices of that platform resolve to it.

#### Scenario: Adapter is resolvable
- **WHEN** the registry is asked for the Samsung Tizen platform identifier
- **THEN** it returns the Samsung Tizen adapter

### Requirement: Declared Samsung capabilities
The Samsung Tizen adapter SHALL declare support for the directional keys, OK, back, home, volume up, volume down, and mute. It SHALL declare a text support flag that reflects its best-effort nature.

#### Scenario: Capabilities include the core button set
- **WHEN** the adapter's capabilities are read
- **THEN** the directional keys, OK, back, home, volume, and mute are present

### Requirement: Token pairing
The Samsung Tizen adapter SHALL obtain a pairing token by connecting so the TV presents its authorization popup, and SHALL return that token for persistence. Later connections SHALL reuse the stored token without re-prompting.

#### Scenario: First pairing obtains a token
- **WHEN** the adapter pairs with a TV and the user authorizes on the TV
- **THEN** the adapter returns a token that can be stored

#### Scenario: Stored token reused
- **WHEN** the adapter connects with a previously stored token
- **THEN** it establishes a session without triggering the authorization popup again

### Requirement: Key mapping
The Samsung Tizen adapter SHALL translate each supported generic key into the corresponding Samsung remote key code when sending over a session.

#### Scenario: Directional key mapped
- **WHEN** a supported directional or select key is sent
- **THEN** the adapter sends the matching Samsung key code to the TV

### Requirement: Best-effort text entry
The Samsung Tizen adapter SHALL attempt to send text to the TV, and SHALL report text as unsupported when the attempt fails or the firmware does not support it, rather than silently discarding the text.

#### Scenario: Text unsupported reported
- **WHEN** a text send fails or the firmware rejects text input
- **THEN** the session reports text-unsupported so the caller can inform the user

### Requirement: Human-readable display name
The Samsung Tizen adapter SHALL expose a human-readable display name, "Samsung Tizen", distinct from its platform identifier, so the UI can present the platform without encoding brand knowledge.

#### Scenario: Display name exposed
- **WHEN** the adapter's display name is read
- **THEN** it is "Samsung Tizen"
- **AND** the platform identifier remains "samsung-tizen"

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

