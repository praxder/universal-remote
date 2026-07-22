## ADDED Requirements

### Requirement: Rebindable action catalog

The application SHALL define a catalog of actions that drives both the screen key bindings and the Keyboard Shortcuts table. Each entry SHALL have a stable identifier, a human-readable label, a flag for whether it is rebindable, and a default key that MAY be empty (no shortcut). The catalog SHALL also record the surface on which each action is active so that each screen binds the right actions; this surface tag SHALL NOT affect conflict detection, which is global. Rebindable entries MAY be reassigned by the user; reserved entries are fixed and MUST NOT be changed. The surfaces SHALL be:

- **Home** — active only on the entry menu: Manage Devices (`d`), Use Remote (`r`), Settings (`s`), Quit (`q`), all rebindable.
- **Global** — active on every screen except the root menu: Go Back (`escape`), rebindable.
- **Remote** — active only on the remote surface: twenty-six rebindable device actions — OK, Back, Home, Volume Up, Volume Down, Mute, Menu, Channel Up, Channel Down, Play, Pause, Play/Pause, Rewind, Fast-forward, Stop, the number keys 0–9, and Text entry (`t`) — plus four **reserved** D-pad directional actions (Up, Down, Left, Right).

The four D-pad directional actions SHALL be reserved: each is fixed to its arrow key with the matching Vim key (`h`/`j`/`k`/`l`) as a fixed alias, and neither key may be reassigned. OK SHALL default to `enter`, Back to `backspace`, Home to `space`, and the number keys to `0`–`9`. The twelve formerly mouse-only keys (Volume Up, Volume Down, Mute, Menu, Channel Up, Channel Down, Play, Pause, Play/Pause, Rewind, Fast-forward, Stop) SHALL default to no shortcut.

The catalog SHALL also include reserved entries for framework keys that are not device actions — Activate Control (`enter`), Command Palette (`ctrl+p`), and focus navigation Tab (`tab`) and Shift+Tab (`shift+tab`) — so the user can see those keys are in use.

#### Scenario: Every rebindable action is catalogued

- **WHEN** the application enumerates its rebindable actions
- **THEN** the catalog contains the four Home actions, the Global Go Back action, and the twenty-six rebindable Remote actions, each with an id, label, surface, and default key

#### Scenario: Reserved entries are catalogued and marked fixed

- **WHEN** the application enumerates its reserved entries
- **THEN** the catalog contains the four D-pad directional actions and the framework keys (Activate Control, Command Palette, and focus navigation Tab and Shift+Tab), each marked as reserved and not rebindable

#### Scenario: Some actions start with no shortcut

- **WHEN** the catalog is read before any customization
- **THEN** the twelve formerly mouse-only remote keys have no default key while every other rebindable action has one

### Requirement: Keyboard Shortcuts screen lists actions and shortcuts

The application SHALL provide a Keyboard Shortcuts screen, reached from the Settings screen. The screen SHALL present a table with one row per catalogued entry — both rebindable and reserved — showing the entry's label and its current shortcut, where the shortcut cell MAY be empty when a rebindable action has none. Reserved entries SHALL be shown as disabled (non-activatable) rows so the user can see the key is in use but cannot change it. Every rebindable row MUST be reachable by keyboard and by mouse, and the user MUST be able to return from the screen to Settings.

#### Scenario: Screen lists all actions

- **WHEN** the user opens the Keyboard Shortcuts screen
- **THEN** it shows a table with a row for every catalogued entry and each row's current shortcut

#### Scenario: Reserved entries are shown disabled

- **WHEN** the table is displayed
- **THEN** the reserved entries (the D-pad directions, Activate Control, and Command Palette) appear as disabled rows that cannot be activated for capture

#### Scenario: Actions without a shortcut show as blank

- **WHEN** a rebindable action has no shortcut assigned
- **THEN** its row is shown with an empty shortcut cell

#### Scenario: Return to Settings

- **WHEN** the user leaves the Keyboard Shortcuts screen
- **THEN** the application returns to the Settings screen

### Requirement: Shortcuts are displayed in a readable form

Every shortcut shown in the table SHALL be rendered as an uppercase label rather than its raw internal key name: modifier-plus-key combinations SHALL be joined with a hyphen (for example `ctrl+p` shown as `CTRL-P`), and named keys SHALL use a short friendly form (for example `space` as `SPACE`, `escape` as `ESC`). A reserved D-pad row SHALL show both its arrow key and its Vim alias (for example `UP` / `K`).

#### Scenario: Modifier combination is shown in friendly form

- **WHEN** a shortcut is a modifier combination such as `ctrl+p`
- **THEN** the table shows it as `CTRL-P`

#### Scenario: Named key is shown in friendly form

- **WHEN** a shortcut is a named key such as `space` or `escape`
- **THEN** the table shows a short uppercase label such as `SPACE` or `ESC`

### Requirement: Assign, clear, or cancel from the capture modal

Activating a rebindable row (Enter or click) SHALL open a capture modal prompting the user to press a key. The next key the user presses — including Escape — SHALL be normalized to its canonical long form and, subject to the conflict and reserved-key rules, assigned as that action's shortcut, after which the modal closes and the row updates. The modal SHALL provide two mouse-only buttons that do not take keyboard focus: a **Cancel** button that closes the modal without changing the shortcut, and a **DEL** button that clears the action's shortcut (leaving it with none) and closes the modal. Because the buttons never hold focus, there SHALL be no keyboard-only way to cancel or clear — every key press is captured as a candidate shortcut.

#### Scenario: Capture assigns a new shortcut

- **WHEN** the user activates a row and presses an available key
- **THEN** that key becomes the action's shortcut, the modal closes, and the row shows the new shortcut

#### Scenario: The DEL button clears a shortcut

- **WHEN** the user activates a row and clicks the DEL button in the capture modal
- **THEN** the action's shortcut is cleared, the modal closes, and the row shows an empty shortcut cell

#### Scenario: The Cancel button leaves the shortcut unchanged

- **WHEN** the user activates a row and clicks the Cancel button in the capture modal
- **THEN** the modal closes and the action's shortcut is unchanged

#### Scenario: Escape is captured as a shortcut

- **WHEN** the user activates a row and presses Escape in the capture modal
- **THEN** Escape is treated as the pressed key and assigned (subject to the conflict and reserved-key rules), not as a cancel

### Requirement: Conflicting shortcuts are rejected

Every shortcut SHALL be unique across the entire application: a key MAY be assigned to at most one action. An assignment SHALL be refused when the chosen key is already used by any other action, regardless of which surface either action belongs to. On refusal the existing shortcut SHALL be left unchanged and the application SHALL show an error toast naming the key and the action that already owns it.

#### Scenario: A key already used by another action is rejected

- **WHEN** the user assigns a key that any other action already uses
- **THEN** the assignment is refused, the action keeps its previous shortcut, and a toast reports that the key is already taken and by which action

#### Scenario: A key free everywhere is accepted

- **WHEN** the user assigns a key that no other action uses
- **THEN** the assignment succeeds and becomes that action's shortcut

### Requirement: Reserved keys cannot be assigned

A new assignment to a key reserved by a fixed catalog entry SHALL be refused with an error toast. The reserved keys SHALL be those held by the reserved entries: the D-pad directional keys (the arrow keys and `h`, `j`, `k`, `l`), Enter (Activate Control), Tab and Shift+Tab (focus navigation), and the command-palette key (`ctrl+p`). A rebindable action's existing default binding SHALL be exempt from this rule so that a default which coincides with a reserved key (for example OK defaulting to Enter) remains valid.

#### Scenario: Assigning a reserved key is refused

- **WHEN** the user tries to assign a rebindable action a reserved key such as `j`, Enter, Tab, or `ctrl+p`
- **THEN** the assignment is refused and a toast explains the key is reserved

#### Scenario: A default on a reserved key remains valid

- **WHEN** a rebindable action's default key is itself a reserved key, such as OK defaulting to Enter
- **THEN** that default binding is honored and is not flagged as reserved

### Requirement: Custom shortcuts apply immediately

When a shortcut is assigned or cleared, the change SHALL take effect immediately without restarting the application: the bindings of every currently mounted screen SHALL be rebuilt so the new shortcut is active and any removed shortcut no longer fires.

#### Scenario: New shortcut works without restart

- **WHEN** the user assigns a formerly-unbound remote key a shortcut and returns to the remote
- **THEN** pressing that key sends the corresponding device key in the same session

#### Scenario: Cleared shortcut stops firing

- **WHEN** the user clears an action's shortcut
- **THEN** the previously bound key no longer triggers that action

### Requirement: Command palette shows a read-only shortcuts view

The application's command palette SHALL offer a single "Keyboard Shortcuts" command. Selecting it SHALL dismiss the palette and open a modal that lists every catalogued action and its current shortcut in readable form. This view SHALL be read-only — it MUST NOT provide any way to assign, clear, or otherwise change a shortcut; editing remains on the Keyboard Shortcuts screen reached from Settings.

#### Scenario: Palette opens the read-only shortcuts view

- **WHEN** the user opens the command palette and selects the Keyboard Shortcuts command
- **THEN** the palette closes and a modal appears listing every action and its current shortcut

#### Scenario: The palette view cannot edit shortcuts

- **WHEN** the read-only shortcuts modal is shown
- **THEN** no row can be activated to change a shortcut and the modal offers no assign or clear affordance
