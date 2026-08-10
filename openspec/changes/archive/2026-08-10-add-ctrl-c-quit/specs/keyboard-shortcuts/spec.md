## ADDED Requirements

### Requirement: Ctrl+C quits immediately from anywhere

The application SHALL exit on a single Ctrl+C press, whichever screen is showing, whether or not a modal is open, and whether or not a text input or text area holds focus. Ctrl+C MUST NOT show a prompt naming another key to quit, and MUST NOT require a second press. Ctrl+Q SHALL continue to quit as well.

Because Ctrl+C takes precedence over the focused widget's own key handling, it SHALL override the framework's Ctrl+C-to-copy behavior inside a text input or text area; copying there falls back to the terminal emulator's own copy. Neither quit key SHALL appear as a footer hint, because the supported 80-column footer has no room for a further hint.

#### Scenario: Ctrl+C quits from a screen

- **WHEN** the user presses Ctrl+C on any screen, including the entry menu
- **THEN** the application exits immediately, with no prompt naming another quit key

#### Scenario: Ctrl+C quits while a modal is open

- **WHEN** the user presses Ctrl+C while any modal is open
- **THEN** the application exits immediately rather than the key being swallowed by the modal

#### Scenario: Ctrl+C quits while the capture modal is reading a key

- **WHEN** the user presses Ctrl+C while the shortcut capture modal is waiting for a key
- **THEN** the application exits immediately and no shortcut is assigned

#### Scenario: Ctrl+C quits while a text field has focus

- **WHEN** the user presses Ctrl+C while a text input or text area has focus
- **THEN** the application exits immediately instead of copying the selected text

#### Scenario: Ctrl+Q still quits

- **WHEN** the user presses Ctrl+Q
- **THEN** the application exits, as it did before Ctrl+C was bound

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

The catalog SHALL also include reserved entries for framework keys that are not device actions — Activate Control (`enter`), Command Palette (`ctrl+p`), focus navigation Tab (`tab`) and Shift+Tab (`shift+tab`), and quit (`ctrl+c`, with `ctrl+q` as a fixed alias) — so the user can see those keys are in use.

#### Scenario: Every rebindable action is catalogued

- **WHEN** the application enumerates its rebindable actions
- **THEN** the catalog contains the four Home actions, the Global Go Back action, and the thirty-two rebindable Remote actions (the twenty-six device actions, the five custom-button activation actions, and the Macros action), each with an id, label, surface, and default key

#### Scenario: Reserved entries are catalogued and marked fixed

- **WHEN** the application enumerates its reserved entries
- **THEN** the catalog contains the four D-pad directional actions, the Configure Custom Button edit-mode action (`e`), and the framework keys (Activate Control, Command Palette, focus navigation Tab and Shift+Tab, and quit — Ctrl+C with Ctrl+Q as a fixed alias), each marked as reserved and not rebindable

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

### Requirement: Keyboard Shortcuts screen lists actions and shortcuts

The application SHALL provide a Keyboard Shortcuts screen, reached from the Settings screen. The screen SHALL present a single table with one row per catalogued entry — both rebindable and reserved — showing the entry's label and its current shortcut, where the shortcut cell MAY be empty when a rebindable action has none. The rows SHALL be grouped by surface (Home, Global, Remote) under a non-activatable heading row per group so the user can see which actions apply where. Reserved entries SHALL be shown as disabled (non-activatable) rows so the user can see the key is in use but cannot change it. Every rebindable row MUST be reachable by keyboard and by mouse, and the user MUST be able to return from the screen to Settings.

#### Scenario: Screen lists all actions

- **WHEN** the user opens the Keyboard Shortcuts screen
- **THEN** it shows a table with a row for every catalogued entry and each row's current shortcut

#### Scenario: Actions are grouped under surface headings

- **WHEN** the table is displayed
- **THEN** the rows appear under Home, Global, and Remote heading rows, and activating a heading row does nothing

#### Scenario: Reserved entries are shown disabled

- **WHEN** the table is displayed
- **THEN** the reserved entries (the D-pad directions, the Configure Custom Button edit-mode key, Activate Control, the Command Palette, focus-navigation Tab and Shift+Tab, and the quit keys Ctrl+C and Ctrl+Q) appear as disabled rows that cannot be activated for capture

#### Scenario: Actions without a shortcut show as blank

- **WHEN** a rebindable action has no shortcut assigned
- **THEN** its row is shown with an empty shortcut cell

#### Scenario: Return to Settings

- **WHEN** the user leaves the Keyboard Shortcuts screen
- **THEN** the application returns to the Settings screen

### Requirement: Shortcuts are displayed in a readable form

Every shortcut shown in the table SHALL be rendered as an uppercase label rather than its raw internal key name: modifier-plus-key combinations SHALL be joined with a hyphen (for example `ctrl+p` shown as `CTRL-P`), and named keys SHALL use a short friendly form (for example `space` as `SPACE`, `escape` as `ESC`). A reserved row that has fixed aliases SHALL show its primary key and every alias, separated by ` / ` — a D-pad row shows its arrow key and its Vim alias (for example `UP` / `K`), and the quit row shows `CTRL-C` / `CTRL-Q`.

#### Scenario: Modifier combination is shown in friendly form

- **WHEN** a shortcut is a modifier combination such as `ctrl+p`
- **THEN** the table shows it as `CTRL-P`

#### Scenario: Named key is shown in friendly form

- **WHEN** a shortcut is a named key such as `space` or `escape`
- **THEN** the table shows a short uppercase label such as `SPACE` or `ESC`

### Requirement: Reserved keys cannot be assigned

A new assignment to a key reserved by a fixed catalog entry SHALL be refused with an error toast. The reserved keys SHALL be those held by the reserved entries: the D-pad directional keys (the arrow keys and `h`, `j`, `k`, `l`), the edit-mode key `e` (Configure Custom Button), Enter (Activate Control), Tab and Shift+Tab (focus navigation), the command-palette key (`ctrl+p`), and the quit keys `ctrl+c` and `ctrl+q`. A rebindable action's existing default binding SHALL be exempt from this rule so that a default which coincides with a reserved key (for example OK defaulting to Enter) remains valid.

#### Scenario: Assigning a reserved key is refused

- **WHEN** the user tries to assign a rebindable action a reserved key such as `j`, `e`, Enter, Tab, `ctrl+p`, or `ctrl+q`
- **THEN** the assignment is refused and a toast explains the key is reserved

#### Scenario: A default on a reserved key remains valid

- **WHEN** a rebindable action's default key is itself a reserved key, such as OK defaulting to Enter
- **THEN** that default binding is honored and is not flagged as reserved
