## MODIFIED Requirements

### Requirement: Rebindable action catalog

The application SHALL define a catalog of actions that drives both the screen key bindings and the Keyboard Shortcuts table. Each entry SHALL have a stable identifier, a human-readable label, a flag for whether it is rebindable, and a default key that MAY be empty (no shortcut). The catalog SHALL also record the surface on which each action is active so that each screen binds the right actions; this surface tag SHALL NOT affect conflict detection, which is global. Rebindable entries MAY be reassigned by the user; reserved entries are fixed and MUST NOT be changed. The surfaces SHALL be:

- **Home** — active only on the entry menu: Manage Devices (`d`), Use Remote (`r`), Settings (`s`), Quit (`q`), all rebindable.
- **Global** — active on every screen except the root menu: Go Back (`escape`), rebindable.
- **Remote** — active only on the remote surface: thirty-one rebindable actions — the twenty-six device actions (OK, Back, Home, Volume Up, Volume Down, Mute, Menu, Channel Up, Channel Down, Play, Pause, Play/Pause, Rewind, Fast-forward, Stop, the number keys 0–9, and Text entry (`t`)) and five custom-button activation actions (Activate Custom Button 1 through 5) — plus four **reserved** D-pad directional actions (Up, Down, Left, Right).

The four D-pad directional actions SHALL be reserved: each is fixed to its arrow key with the matching Vim key (`h`/`j`/`k`/`l`) as a fixed alias, and neither key may be reassigned. OK SHALL default to `enter`, Back to `backspace`, Home to `space`, and the number keys to `0`–`9`. The twelve formerly mouse-only keys (Volume Up, Volume Down, Mute, Menu, Channel Up, Channel Down, Play, Pause, Play/Pause, Rewind, Fast-forward, Stop) SHALL default to no shortcut.

The five custom-button activation actions SHALL default to no shortcut. Each activation action, when triggered on the remote, SHALL behave exactly like clicking the matching custom button — it activates the button rather than sending a device key, and it is not tied to any particular device.

The catalog SHALL also include reserved entries for framework keys that are not device actions — Activate Control (`enter`), Command Palette (`ctrl+p`), and focus navigation Tab (`tab`) and Shift+Tab (`shift+tab`) — so the user can see those keys are in use.

#### Scenario: Every rebindable action is catalogued

- **WHEN** the application enumerates its rebindable actions
- **THEN** the catalog contains the four Home actions, the Global Go Back action, and the thirty-one rebindable Remote actions (the twenty-six device actions and the five custom-button activation actions), each with an id, label, surface, and default key

#### Scenario: Reserved entries are catalogued and marked fixed

- **WHEN** the application enumerates its reserved entries
- **THEN** the catalog contains the four D-pad directional actions and the framework keys (Activate Control, Command Palette, and focus navigation Tab and Shift+Tab), each marked as reserved and not rebindable

#### Scenario: Some actions start with no shortcut

- **WHEN** the catalog is read before any customization
- **THEN** the twelve formerly mouse-only remote keys and the five custom-button activation actions have no default key, while every other rebindable action has one

#### Scenario: A custom-button activation action mirrors a click

- **WHEN** the user assigns a shortcut to a custom-button activation action and presses it on the remote
- **THEN** the matching custom button is activated exactly as if it had been clicked
