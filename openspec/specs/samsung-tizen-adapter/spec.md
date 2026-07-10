# samsung-tizen-adapter Specification

## Purpose
TBD - created by archiving change scaffold-samsung-remote. Update Purpose after archive.
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

