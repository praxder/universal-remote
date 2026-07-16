## MODIFIED Requirements

### Requirement: Low-latency key dispatch with fallback
The Fire TV adapter SHALL prefer a faster device input path for keys that support it, and SHALL fall back to the standard key-event path for any other key or when the faster path is unavailable, without changing which action a key sends. The faster path SHALL cover the directional keys, OK, back, volume, mute, the number pad, home, menu, and the media-transport keys — play, pause, play/pause, stop, rewind, and fast-forward. The scancode used for each key SHALL be one confirmed against the device's input node rather than assumed.

#### Scenario: Fast path used when available
- **WHEN** a key the faster input path supports is sent over a session to a device that exposes that path
- **THEN** the adapter dispatches it over the faster path
- **AND** the action sent is the one that key maps to

#### Scenario: Home, menu, and media keys use the fast path
- **WHEN** the home key, the menu key, or a media-transport key (play, pause, play/pause, stop, rewind, or fast-forward) is sent over a session to a device that exposes the faster input path
- **THEN** the adapter dispatches it over the faster path rather than the standard key-event path
- **AND** the action sent is the one that key maps to

#### Scenario: Fallback preserves behaviour
- **WHEN** the device exposes no faster input path
- **THEN** the adapter dispatches every key over the standard key-event path
- **AND** each key still sends its mapped action
