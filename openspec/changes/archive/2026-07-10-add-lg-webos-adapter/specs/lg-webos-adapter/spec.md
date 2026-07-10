## ADDED Requirements

### Requirement: LG WebOS adapter registration
The system SHALL provide an adapter for the LG WebOS platform, registered under a stable platform identifier so devices of that platform resolve to it.

#### Scenario: Adapter is resolvable
- **WHEN** the registry is asked for the LG WebOS platform identifier
- **THEN** it returns the LG WebOS adapter

### Requirement: Declared LG WebOS capabilities
The LG WebOS adapter SHALL declare support for the directional keys, OK, back, home, volume up, volume down, mute, and power. It SHALL declare its text and power-on support flags.

#### Scenario: Capabilities include the core button set
- **WHEN** the adapter's capabilities are read
- **THEN** the directional keys, OK, back, home, volume, mute, and power are present
- **AND** no device connection is required to read them

### Requirement: Client-key pairing
The LG WebOS adapter SHALL obtain a pairing credential (a client-key) by connecting so the TV presents its on-screen authorization prompt, and SHALL return that client-key for persistence. Later connections SHALL reuse the stored client-key without re-prompting.

#### Scenario: First pairing obtains a client-key
- **WHEN** the adapter pairs with a TV and the user accepts the prompt on the TV
- **THEN** the adapter returns a client-key that can be stored

#### Scenario: Stored client-key reused
- **WHEN** the adapter connects with a previously stored client-key
- **THEN** it establishes a session without triggering the authorization prompt again

### Requirement: Key mapping
The LG WebOS adapter SHALL translate each supported generic key into the corresponding LG WebOS action when sending over a session, so callers reference only generic keys.

#### Scenario: Directional key mapped
- **WHEN** a supported directional or select key is sent
- **THEN** the adapter sends the matching LG WebOS action to the TV

#### Scenario: Power key mapped
- **WHEN** the power key is sent over a session
- **THEN** the adapter powers the TV off

#### Scenario: Unsupported key rejected
- **WHEN** a caller sends a key the adapter does not declare
- **THEN** the session reports the key as unsupported and does not send an arbitrary substitute

### Requirement: Best-effort text entry
The LG WebOS adapter SHALL attempt to send text to the TV, and SHALL report text as unsupported when the attempt fails, rather than silently discarding the text.

#### Scenario: Text unsupported reported
- **WHEN** a text send fails
- **THEN** the session reports text-unsupported so the caller can inform the user

### Requirement: Power handling
The LG WebOS adapter SHALL power the TV off with the power key while connected, and SHALL attempt power-on via a Wake-on-LAN magic packet to the stored MAC address as a best-effort action.

#### Scenario: Power off while on
- **WHEN** power is requested while the TV is reachable
- **THEN** the adapter sends the power action

#### Scenario: Best-effort power on
- **WHEN** power-on is requested and a MAC address is stored
- **THEN** the adapter sends a Wake-on-LAN magic packet to that MAC
- **AND** reports the action as best-effort rather than guaranteed
