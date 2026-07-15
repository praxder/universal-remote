## MODIFIED Requirements

### Requirement: Generic key vocabulary

The system SHALL define a platform-agnostic set of remote keys that all callers use, independent of any TV brand. The vocabulary MUST cover directional navigation (up, down, left, right), select/OK, back, home, volume up, volume down, mute, a menu key, channel up and channel down, the media-transport keys play, pause, play/pause, rewind, fast-forward, and stop, and the number keys 0 through 9. An adapter MAY declare any subset of this vocabulary; keys an adapter does not declare are simply unsupported on that platform.

#### Scenario: Callers reference generic keys only

- **WHEN** the UI or store issues a remote action
- **THEN** it references a generic key value, never a brand-specific key code

#### Scenario: Vocabulary spans navigation, media, and numbers

- **WHEN** a caller enumerates the generic key vocabulary
- **THEN** it includes the directional, select, back, home, volume, and mute keys
- **AND** it includes a menu key, channel up and channel down, the media-transport keys (play, pause, play/pause, rewind, fast-forward, stop), and the number keys 0 through 9

#### Scenario: Adapter declares a subset

- **WHEN** an adapter supports only some of the vocabulary
- **THEN** it declares only the keys its platform supports
- **AND** the keys it omits are reported as unsupported without error
