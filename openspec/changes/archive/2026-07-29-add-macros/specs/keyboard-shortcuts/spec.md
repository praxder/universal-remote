## MODIFIED Requirements

### Requirement: Rebindable action catalog

The application SHALL define a catalog of actions that drives both the screen key bindings and the Keyboard Shortcuts table. Each entry SHALL have a stable identifier, a human-readable label, a flag for whether it is rebindable, and a default key that MAY be empty (no shortcut). The catalog SHALL also record the surface on which each action is active so that each screen binds the right actions; this surface tag SHALL NOT affect conflict detection, which is global. Rebindable entries MAY be reassigned by the user; reserved entries are fixed and MUST NOT be changed. The surfaces SHALL be:

- **Home** — active only on the entry menu: Manage Devices (`d`), Use Remote (`r`), Settings (`s`), Quit (`q`), all rebindable.
- **Global** — active on every screen except the root menu: Go Back (`escape`), rebindable.
- **Remote** — active only on the remote surface: thirty-two rebindable actions — the twenty-six device actions (OK, Back, Home, Volume Up, Volume Down, Mute, Menu, Channel Up, Channel Down, Play, Pause, Play/Pause, Rewind, Fast-forward, Stop, the number keys 0–9, and Text entry (`t`)), five custom-button activation actions (Activate Custom Button 1 through 5), and one Macros action that opens the macros list — plus four **reserved** D-pad directional actions (Up, Down, Left, Right) and one **reserved** edit-mode action, Configure Custom Button, fixed to `e`.

The four D-pad directional actions SHALL be reserved: each is fixed to its arrow key with the matching Vim key (`h`/`j`/`k`/`l`) as a fixed alias, and neither key may be reassigned. OK SHALL default to `enter`, Back to `backspace`, Home to `space`, and the number keys to `0`–`9`. The twelve formerly mouse-only keys (Volume Up, Volume Down, Mute, Menu, Channel Up, Channel Down, Play, Pause, Play/Pause, Rewind, Fast-forward, Stop) SHALL default to no shortcut.

The five custom-button activation actions SHALL default to no shortcut. Each activation action, when triggered on the remote, SHALL behave exactly like clicking the matching custom button — it activates the button rather than sending a device key, and it is not tied to any particular device.

The Macros action SHALL default to no shortcut and SHALL be kept out of the footer, because the supported 80-column footer has no room for a further hint. When triggered on the remote it SHALL behave exactly like clicking the Macros button — opening the macros list — so the macros capability is reachable by keyboard as well as by mouse.

The Configure Custom Button action SHALL be reserved and fixed to `e`: it toggles custom-button edit-mode — arming it, or disarming it when already armed (see the remote surface's edit gesture) — and its key MUST NOT be reassigned. It SHALL be catalogued so it appears as a fixed row in the Keyboard Shortcuts table.

The catalog SHALL also include reserved entries for framework keys that are not device actions — Activate Control (`enter`), Command Palette (`ctrl+p`), and focus navigation Tab (`tab`) and Shift+Tab (`shift+tab`) — so the user can see those keys are in use.

#### Scenario: Every rebindable action is catalogued

- **WHEN** the application enumerates its rebindable actions
- **THEN** the catalog contains the four Home actions, the Global Go Back action, and the thirty-two rebindable Remote actions (the twenty-six device actions, the five custom-button activation actions, and the Macros action), each with an id, label, surface, and default key

#### Scenario: Reserved entries are catalogued and marked fixed

- **WHEN** the application enumerates its reserved entries
- **THEN** the catalog contains the four D-pad directional actions, the Configure Custom Button edit-mode action (`e`), and the framework keys (Activate Control, Command Palette, and focus navigation Tab and Shift+Tab), each marked as reserved and not rebindable

#### Scenario: Some actions start with no shortcut

- **WHEN** the catalog is read before any customization
- **THEN** the twelve formerly mouse-only remote keys, the five custom-button activation actions, and the Macros action have no default key, while every other rebindable action has one

#### Scenario: A custom-button activation action mirrors a click

- **WHEN** the user assigns a shortcut to a custom-button activation action and presses it on the remote
- **THEN** the matching custom button is activated exactly as if it had been clicked

#### Scenario: The Macros action mirrors clicking the Macros button

- **WHEN** the user assigns a shortcut to the Macros action and presses it on the remote
- **THEN** the macros list opens exactly as if the Macros button had been clicked

#### Scenario: The Macros action stays out of the footer

- **WHEN** the user assigns a shortcut to the Macros action and views the remote
- **THEN** the footer does not gain a hint for it, so the existing hints still fit the supported 80-column width
