## ADDED Requirements

### Requirement: Remote screen status bar identifies the active device
While Use Remote mode is showing the on-screen remote, the top status bar SHALL identify the active device as `Name: <name> • Type: <type> • IP: <ip>`, where `<name>` is the device's name, `<ip>` is its IP address, and `<type>` is the platform's human-readable label — the same label used for the device-type picker on the add/edit screen, not the raw platform identifier. The status bar SHALL NOT include any other prefix or text.

#### Scenario: Status bar shows name, type, and IP
- **WHEN** the user opens Use Remote for a device named "Living Room TV" on the `androidtv` platform (human-readable label "Android TV") at IP 192.168.20.51
- **THEN** the status bar reads `Name: Living Room TV • Type: Android TV • IP: 192.168.20.51`

#### Scenario: Type uses the human-readable label
- **WHEN** the remote is shown for a device
- **THEN** the status bar's Type field displays the platform's human-readable label rather than the raw platform identifier
