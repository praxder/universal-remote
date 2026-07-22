## ADDED Requirements

### Requirement: Rebindable action catalog

The application SHALL define a catalog of rebindable actions. Each action SHALL have a stable identifier, a human-readable label, a scope, and a default key that MAY be empty (no shortcut). The scopes SHALL be:

- **Home** — active only on the entry menu: Manage Devices (default `d`), Use Remote (default `r`), Settings (default `s`), Quit (default `q`).
- **Global** — active on every screen except the root menu: Go Back (default `escape`).
- **Remote** — active only on the remote surface: all 29 device keys (Up, Down, Left, Right, OK, Back, Home, Volume Up, Volume Down, Mute, Menu, Channel Up, Channel Down, Play, Pause, Play/Pause, Rewind, Fast-forward, Stop, and number keys 0–9) plus Text entry (default `t`).

Directional and OK/Back/Home/digit remote actions SHALL keep their current default keys; the twelve click-only keys (Volume Up, Volume Down, Mute, Menu, Channel Up, Channel Down, Play, Pause, Play/Pause, Rewind, Fast-forward, Stop) SHALL default to no shortcut.

#### Scenario: Every rebindable action is catalogued

- **WHEN** the application enumerates its rebindable actions
- **THEN** the catalog contains the four Home actions, the Global Go Back action, and the thirty Remote actions, each with an id, label, scope, and default key

#### Scenario: Some actions start with no shortcut

- **WHEN** the catalog is read before any customization
- **THEN** the twelve click-only remote keys have no default key while every other action has one

### Requirement: Keyboard Shortcuts screen lists actions and shortcuts

The application SHALL provide a Keyboard Shortcuts screen, reached from the Settings screen. The screen SHALL present a table with one row per catalogued action showing the action's label and its current shortcut, where the shortcut cell MAY be empty when the action has none. Every row MUST be reachable by keyboard and by mouse, and the user MUST be able to return from the screen to Settings.

#### Scenario: Screen lists all actions

- **WHEN** the user opens the Keyboard Shortcuts screen
- **THEN** it shows a table with a row for every catalogued action and each row's current shortcut

#### Scenario: Actions without a shortcut show as blank

- **WHEN** an action has no shortcut assigned
- **THEN** its row is shown with an empty shortcut cell

#### Scenario: Return to Settings

- **WHEN** the user leaves the Keyboard Shortcuts screen
- **THEN** the application returns to the Settings screen

### Requirement: Assign or clear a shortcut by capture

Activating a row (Enter or click) SHALL open a capture modal prompting the user to press a key. The next key the user presses SHALL be normalized to its canonical long form and, subject to the conflict and reserved-key rules, assigned as that action's shortcut, after which the modal closes and the row updates. Pressing Delete or Escape in the capture modal SHALL clear the action's shortcut (leaving it with none) and close the modal.

#### Scenario: Capture assigns a new shortcut

- **WHEN** the user activates a row and presses an available key
- **THEN** that key becomes the action's shortcut, the modal closes, and the row shows the new shortcut

#### Scenario: Delete clears a shortcut

- **WHEN** the user activates a row and presses Delete in the capture modal
- **THEN** the action's shortcut is cleared, the modal closes, and the row shows an empty shortcut cell

#### Scenario: Escape clears a shortcut

- **WHEN** the user activates a row and presses Escape in the capture modal
- **THEN** the action's shortcut is cleared and the modal closes

### Requirement: Conflicting shortcuts are rejected

An assignment SHALL be refused when the chosen key is already used by another action that can be active on the same screen. On refusal the existing shortcut SHALL be left unchanged and the application SHALL show an error toast naming the key and the action that already owns it. Actions whose scopes never share a screen (Home versus Remote) MAY use the same key without conflict.

#### Scenario: Reused key on the same surface is rejected

- **WHEN** the user assigns a key that another action in an overlapping scope already uses
- **THEN** the assignment is refused, the action keeps its previous shortcut, and a toast reports that the key is already taken and by which action

#### Scenario: Go Back cannot collide with a remote key

- **WHEN** the user assigns Go Back a key already used by a remote key
- **THEN** the assignment is refused with a toast, because Go Back is active on the remote surface

#### Scenario: Home and Remote may share a key

- **WHEN** the user assigns a Remote action a key that a Home action also uses
- **THEN** the assignment succeeds, because Home and Remote actions are never active on the same screen

### Requirement: Reserved keys cannot be assigned

A new assignment to a key reserved by non-rebindable machinery SHALL be refused with an error toast. The reserved keys SHALL include the focus-navigation keys (the arrow keys and `h`, `j`, `k`, `l`), Enter (activates the focused control), and the command-palette key (`ctrl+p`). An action's existing default binding SHALL be exempt from this rule so that defaults which coincide with reserved keys (for example, the remote Up key defaulting to the Up arrow) remain valid.

#### Scenario: Assigning a reserved key is refused

- **WHEN** the user tries to assign an action a focus-navigation key such as `j`, Enter, or `ctrl+p`
- **THEN** the assignment is refused and a toast explains the key is reserved

#### Scenario: Defaults on reserved keys remain valid

- **WHEN** an action's default key is itself a reserved key, such as the remote Up key on the Up arrow
- **THEN** that default binding is honored and is not flagged as reserved

### Requirement: Custom shortcuts apply immediately

When a shortcut is assigned or cleared, the change SHALL take effect immediately without restarting the application: the bindings of every currently mounted screen SHALL be rebuilt so the new shortcut is active and any removed shortcut no longer fires.

#### Scenario: New shortcut works without restart

- **WHEN** the user assigns a formerly-unbound remote key a shortcut and returns to the remote
- **THEN** pressing that key sends the corresponding device key in the same session

#### Scenario: Cleared shortcut stops firing

- **WHEN** the user clears an action's shortcut
- **THEN** the previously bound key no longer triggers that action
