## MODIFIED Requirements

### Requirement: Declared Samsung capabilities
The Samsung Tizen adapter SHALL declare support for the directional keys, OK, back, home, volume up, volume down, and mute. It SHALL declare a text support flag that reflects its best-effort nature.

#### Scenario: Capabilities include the core button set
- **WHEN** the adapter's capabilities are read
- **THEN** the directional keys, OK, back, home, volume, and mute are present

## REMOVED Requirements

### Requirement: Power handling
**Reason**: The power feature has been removed from the app. Power-off via the power key and best-effort Wake-on-LAN power-on are no longer offered; users power TVs on and off with the physical remote.
**Migration**: None. The stored MAC address that fed Wake-on-LAN is also removed from the device model.
