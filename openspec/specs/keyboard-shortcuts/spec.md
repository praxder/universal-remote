# keyboard-shortcuts Specification

## Purpose
TBD - created by syncing change add-custom-keyboard-shortcuts. Update Purpose after archive.
## Requirements
### Requirement: Rebindable action catalog

The application SHALL define a catalog of actions that drives both the screen key bindings and the Keyboard Shortcuts table. Each entry SHALL have a stable identifier, a human-readable label, a flag for whether it is rebindable, and a default key that MAY be empty (no shortcut). The catalog SHALL also record the surface on which each action is active so that each screen binds the right actions; this surface tag SHALL NOT affect conflict detection, which is global. Rebindable entries MAY be reassigned by the user; reserved entries are fixed and MUST NOT be changed. The surfaces SHALL be:

- **Home** — active only on the entry menu: Manage Devices (`d`), Use Remote (`r`), Settings (`s`), Quit (`q`), all rebindable.
- **Global** — active on every screen except the root menu: Go Back (`escape`), rebindable.
- **Remote** — active only on the remote surface: thirty-one rebindable actions — the twenty-six device actions (OK, Back, Home, Volume Up, Volume Down, Mute, Menu, Channel Up, Channel Down, Play, Pause, Play/Pause, Rewind, Fast-forward, Stop, the number keys 0–9, and Text entry (`t`)) and five custom-button activation actions (Activate Custom Button 1 through 5) — plus four **reserved** D-pad directional actions (Up, Down, Left, Right) and one **reserved** edit-mode action, Configure Custom Button, fixed to `e`.

The four D-pad directional actions SHALL be reserved: each is fixed to its arrow key with the matching Vim key (`h`/`j`/`k`/`l`) as a fixed alias, and neither key may be reassigned. OK SHALL default to `enter`, Back to `backspace`, Home to `space`, and the number keys to `0`–`9`. The twelve formerly mouse-only keys (Volume Up, Volume Down, Mute, Menu, Channel Up, Channel Down, Play, Pause, Play/Pause, Rewind, Fast-forward, Stop) SHALL default to no shortcut.

The five custom-button activation actions SHALL default to no shortcut. Each activation action, when triggered on the remote, SHALL behave exactly like clicking the matching custom button — it activates the button rather than sending a device key, and it is not tied to any particular device.

The Configure Custom Button action SHALL be reserved and fixed to `e`: it toggles custom-button edit-mode — arming it, or disarming it when already armed (see the remote surface's edit gesture) — and its key MUST NOT be reassigned. It SHALL be catalogued so it appears as a fixed row in the Keyboard Shortcuts table.

The catalog SHALL also include reserved entries for framework keys that are not device actions — Activate Control (`enter`), Command Palette (`ctrl+p`), and focus navigation Tab (`tab`) and Shift+Tab (`shift+tab`) — so the user can see those keys are in use.

#### Scenario: Every rebindable action is catalogued

- **WHEN** the application enumerates its rebindable actions
- **THEN** the catalog contains the four Home actions, the Global Go Back action, and the thirty-one rebindable Remote actions (the twenty-six device actions and the five custom-button activation actions), each with an id, label, surface, and default key

#### Scenario: Reserved entries are catalogued and marked fixed

- **WHEN** the application enumerates its reserved entries
- **THEN** the catalog contains the four D-pad directional actions, the Configure Custom Button edit-mode action (`e`), and the framework keys (Activate Control, Command Palette, and focus navigation Tab and Shift+Tab), each marked as reserved and not rebindable

#### Scenario: Some actions start with no shortcut

- **WHEN** the catalog is read before any customization
- **THEN** the twelve formerly mouse-only remote keys and the five custom-button activation actions have no default key, while every other rebindable action has one

#### Scenario: A custom-button activation action mirrors a click

- **WHEN** the user assigns a shortcut to a custom-button activation action and presses it on the remote
- **THEN** the matching custom button is activated exactly as if it had been clicked

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

A new assignment to a key reserved by a fixed catalog entry SHALL be refused with an error toast. The reserved keys SHALL be those held by the reserved entries: the D-pad directional keys (the arrow keys and `h`, `j`, `k`, `l`), the edit-mode key `e` (Configure Custom Button), Enter (Activate Control), Tab and Shift+Tab (focus navigation), and the command-palette key (`ctrl+p`). A rebindable action's existing default binding SHALL be exempt from this rule so that a default which coincides with a reserved key (for example OK defaulting to Enter) remains valid.

#### Scenario: Assigning a reserved key is refused

- **WHEN** the user tries to assign a rebindable action a reserved key such as `j`, `e`, Enter, Tab, or `ctrl+p`
- **THEN** the assignment is refused and a toast explains the key is reserved

#### Scenario: A default on a reserved key remains valid

- **WHEN** a rebindable action's default key is itself a reserved key, such as OK defaulting to Enter
- **THEN** that default binding is honored and is not flagged as reserved

### Requirement: Overrides on newly reserved keys are dropped on load

A key MAY become reserved after a user has already assigned it to a rebindable action — for example `e` was assignable before it was reserved for custom-button edit-mode. When saved shortcut overrides are loaded, any override whose key is now reserved SHALL be dropped so it cannot shadow the reserved binding, and the affected action SHALL revert to its default key. The pruning SHALL only affect overrides whose key is reserved; every other saved override SHALL load unchanged. When pruning removes any override, the cleaned override set SHALL be persisted so the stale binding does not reappear on the next run.

#### Scenario: A stale override on a now-reserved key is dropped

- **WHEN** the application loads saved overrides that bind a rebindable action to a key that is now reserved
- **THEN** that override is dropped, the action reverts to its default key, and the reserved binding takes effect

#### Scenario: Free-key overrides are preserved

- **WHEN** the application loads saved overrides where some keys are reserved and others are not
- **THEN** the overrides on non-reserved keys are kept and only the reserved-key overrides are dropped

#### Scenario: The cleaned set is persisted

- **WHEN** loading drops one or more stale reserved-key overrides
- **THEN** the pruned override set is written back so the dropped bindings stay gone on the next run

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

### Requirement: Lone modifier keys cannot be assigned

A shortcut MUST combine any modifier with a base key; a lone modifier press SHALL NOT be assignable. When the capture modal receives a bare modifier key — a left or right Shift, Control, Alt, Super, Hyper, or Meta press, or an ISO level-3 / level-5 shift — the modal SHALL silently ignore it: no shortcut is assigned, the action's existing shortcut is left unchanged, the modal stays open awaiting a real key, and no error is shown. This is because the terminal reports key presses only, never releases: a modifier pressed as the start of a combination (Alt, then A) arrives as its own press event before the combination, so treating it as an error would spuriously reject a valid combo. A modifier combined with a base key (for example `ctrl+b`) is a normal candidate shortcut and SHALL be assignable subject to the conflict and reserved-key rules. The set of lone-modifier keys SHALL match the key names the terminal keyboard protocol delivers when a modifier is pressed on its own, so the check matches what the modal actually receives rather than a shorthand the terminal never sends.

#### Scenario: A lone modifier press is ignored

- **WHEN** the user activates a row and presses only a modifier key (such as Alt or Shift) in the capture modal
- **THEN** no shortcut is assigned, the action keeps its previous shortcut, the capture modal stays open, and no error is shown

#### Scenario: A modifier combined with a base key is accepted

- **WHEN** the user activates a row and presses a modifier-plus-key combination such as `ctrl+b` that no other action uses
- **THEN** the combination becomes the action's shortcut, the modal closes, and the row shows it

#### Scenario: The check matches the protocol's delivered names

- **WHEN** the terminal reports a modifier-only press as its protocol key name (such as `left_alt` or `iso_level3_shift`)
- **THEN** that name is recognized as a lone modifier and ignored, not treated as an ordinary assignable key

### Requirement: Stale lone-modifier overrides are dropped on load

A lone-modifier key MAY have been persisted as an override before it was rejected — the earlier guard used key names the terminal never delivers, so bare modifiers were assignable and could be saved. When saved shortcut overrides are loaded, any override whose key is a lone modifier SHALL be dropped so it cannot bind a modifier press to an action, and the affected action SHALL revert to its default key. Every override whose key is not a lone modifier SHALL load unchanged. When pruning removes any override, the cleaned override set SHALL be persisted so the stale binding does not reappear on the next run.

#### Scenario: A stale lone-modifier override is dropped

- **WHEN** the application loads saved overrides that bind an action to a lone modifier key
- **THEN** that override is dropped and the action reverts to its default key

#### Scenario: Non-modifier overrides are preserved

- **WHEN** the application loads saved overrides where some keys are lone modifiers and others are ordinary keys or modifier combinations
- **THEN** the ordinary and combination overrides are kept and only the lone-modifier overrides are dropped

#### Scenario: The cleaned set is persisted

- **WHEN** loading drops one or more lone-modifier overrides
- **THEN** the pruned override set is written back so the dropped bindings stay gone on the next run

