## MODIFIED Requirements

### Requirement: Low-latency key dispatch with fallback
The Fire TV adapter SHALL prefer a faster device path for keys that support one, and SHALL fall back to the standard key-event path for any other key or when a faster path is unavailable, without changing which action a key sends. It SHALL recognise more than one faster path: an evdev input-node path (`sendevent`) covering the directional keys, OK, back, volume, mute, the number pad, home, and menu; and a media-session dispatch path covering the transport keys — play, pause, play/pause, stop, rewind, and fast-forward. The evdev scancodes for each key, including home and menu, SHALL be ones confirmed against the device's input node rather than assumed.

#### Scenario: Evdev fast path used when available
- **WHEN** a key the evdev input node supports is sent over a session to a device that exposes that node
- **THEN** the adapter dispatches it over the evdev path
- **AND** the action sent is the one that key maps to

#### Scenario: Home and menu use the evdev fast path
- **WHEN** the home or menu key is sent over a session to a device that exposes the evdev input node
- **THEN** the adapter dispatches it over the evdev path rather than the standard key-event path
- **AND** the action sent is the home or menu action respectively

#### Scenario: Media-transport keys use the media-session path
- **WHEN** a media-transport key — play, pause, play/pause, stop, rewind, or fast-forward — is sent over a session
- **THEN** the adapter dispatches it over the media-session dispatch path rather than the standard key-event path
- **AND** the action sent is the one that key maps to

#### Scenario: Fallback preserves behaviour
- **WHEN** a key has no faster-path mapping, or the device exposes no evdev input node
- **THEN** the adapter dispatches it over the standard key-event path
- **AND** the key still sends its mapped action
