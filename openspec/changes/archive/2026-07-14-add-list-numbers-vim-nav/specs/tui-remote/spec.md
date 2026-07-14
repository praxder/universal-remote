## ADDED Requirements

### Requirement: Numbered device lists and digit selection

Both device-selection lists — the Manage Devices list and the Use Remote device picker — SHALL prefix each saved device row with its 1-based position followed by a period and a space (for example, `1. Apple TV`, `2. Android TV`). The numbering SHALL reflect the order in which the devices are listed and SHALL count only saved devices; the `+ Add` entry SHALL NOT be numbered. Pressing a digit key `1` through `9` while such a list is showing SHALL act on the device at that position exactly as selecting that row does — opening it for editing on the Manage Devices list and beginning the connect/pair flow on the Use Remote picker. A digit that does not correspond to a listed device SHALL do nothing. Numbering is a display and shortcut concern only: it SHALL NOT change the stored device name.

#### Scenario: Manage Devices rows are numbered

- **WHEN** the user opens Manage Devices with one or more saved devices
- **THEN** each saved device row is shown prefixed with its 1-based position and a period (the first device reads `1. <name>`)
- **AND** the `+ Add` entry is shown without a number

#### Scenario: Use Remote picker rows are numbered

- **WHEN** the user opens Use Remote with one or more saved devices
- **THEN** each device in the picker is shown prefixed with its 1-based position and a period

#### Scenario: Digit opens the device on Manage Devices

- **WHEN** the Manage Devices list is showing and the user presses a digit matching a listed device's position
- **THEN** that device opens in the edit flow, the same as selecting its row

#### Scenario: Digit selects the device on Use Remote

- **WHEN** the Use Remote picker is showing and the user presses a digit matching a listed device's position
- **THEN** that device begins the connect/pair flow, the same as selecting its row

#### Scenario: Out-of-range digit does nothing

- **WHEN** a device list is showing and the user presses a digit greater than the number of listed devices
- **THEN** nothing happens and no screen is opened

### Requirement: Vim-style menu and list navigation

Every screen whose menu items or list rows are navigable with the arrow keys SHALL also be navigable with the Vim direction keys `h`, `j`, `k`, and `l`, mirroring the arrow keys: `k` and `h` move to the previous item (as Up and Left do) and `j` and `l` move to the next item (as Down and Right do). This SHALL apply to the entry menu, both device-selection lists, and the delete-confirmation dialog. Text-entry screens — the add and edit device form — SHALL continue to move focus between fields with the arrow keys only, so that `h`, `j`, `k`, and `l` typed into an input fill that input rather than moving focus.

#### Scenario: Vim keys move through the entry menu

- **WHEN** the entry menu is showing and the user presses `j` or `k`
- **THEN** focus moves to the next or previous mode button, the same as Down or Up

#### Scenario: Vim keys move through a device list

- **WHEN** a device-selection list is showing and the user presses `j` or `k`
- **THEN** the highlight moves to the next or previous row, the same as Down or Up

#### Scenario: Vim keys move within the delete-confirmation dialog

- **WHEN** the delete-confirmation dialog is showing and the user presses `h`, `j`, `k`, or `l`
- **THEN** focus moves between the confirm and cancel actions, the same as the arrow keys

#### Scenario: Vim letters type into the add/edit form

- **WHEN** an input on the add or edit device form is focused and the user types `h`, `j`, `k`, or `l`
- **THEN** the character is entered into the input and focus does not move

## MODIFIED Requirements

### Requirement: Keyboard control of the remote
The remote SHALL be fully operable from the keyboard, mapping both the arrow keys and the Vim keys `h`, `j`, `k`, and `l` to the D-pad — `h` and Left send LEFT, `j` and Down send DOWN, `k` and Up send UP, `l` and Right send RIGHT — Enter to OK, Escape to Back, and the Space bar to the Home key. Because `h` now sends the LEFT direction, the Home key SHALL no longer be bound to `h`; the on-screen Home button remains clickable with the mouse.

#### Scenario: Arrow key drives D-pad
- **WHEN** the user presses an arrow key while the remote is focused and no text field is active
- **THEN** the matching directional key is sent

#### Scenario: Vim key drives D-pad
- **WHEN** the user presses `h`, `j`, `k`, or `l` while the remote is focused and no text field is active
- **THEN** LEFT, DOWN, UP, or RIGHT is sent, respectively

#### Scenario: Enter and Escape mapped
- **WHEN** the user presses Enter or Escape while the remote is focused and no text field is active
- **THEN** OK or Back is sent, respectively

#### Scenario: Space sends Home
- **WHEN** the user presses the Space bar while the remote is focused and no text field is active
- **THEN** the Home key is sent
