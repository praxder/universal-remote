## MODIFIED Requirements

### Requirement: Declared LG WebOS capabilities
The LG WebOS adapter SHALL declare support for the directional keys, OK, back, home, volume up, volume down, and mute. It SHALL declare its text support flag.

#### Scenario: Capabilities include the core button set
- **WHEN** the adapter's capabilities are read
- **THEN** the directional keys, OK, back, home, volume, and mute are present
- **AND** no device connection is required to read them

### Requirement: Key mapping
The LG WebOS adapter SHALL translate each supported generic key into the corresponding LG WebOS action when sending over a session, so callers reference only generic keys.

#### Scenario: Directional key mapped
- **WHEN** a supported directional or select key is sent
- **THEN** the adapter sends the matching LG WebOS action to the TV

#### Scenario: Unsupported key rejected
- **WHEN** a caller sends a key the adapter does not declare
- **THEN** the session reports the key as unsupported and does not send an arbitrary substitute

## REMOVED Requirements

### Requirement: Power handling
**Reason**: The power feature has been removed from the app. Power-off via the power key and best-effort Wake-on-LAN power-on are no longer offered; users power TVs on and off with the physical remote.
**Migration**: None. The stored MAC address that fed Wake-on-LAN is also removed from the device model.
