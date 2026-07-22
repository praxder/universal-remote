## MODIFIED Requirements

### Requirement: Menu-driven entry with two modes
The application SHALL launch into a menu offering two modes: Manage Devices and Use Remote. Both modes MUST be reachable by keyboard and by mouse. The menu SHALL also present a Settings entry point — a "Settings" button docked in the bottom-left corner of the screen, plus an `s` key binding — that opens the Settings screen. The Settings entry point MUST be reachable by keyboard (the `s` key) and by mouse (clicking the button). Adding the Settings entry point SHALL NOT change the centered layout of the existing menu content (title, mode buttons, and movie quote). The menu's key bindings — Manage Devices (`d`), Use Remote (`r`), Settings (`s`), and Quit (`q`) — SHALL be the default shortcuts of rebindable Home actions that the user MAY change via the keyboard-shortcuts capability; the docked Settings button and the mode buttons remain operable by mouse regardless of the current key bindings.

#### Scenario: Menu offers both modes
- **WHEN** the application starts
- **THEN** it shows a menu with Manage Devices and Use Remote options

#### Scenario: Mode reachable by keyboard and mouse
- **WHEN** the user selects a mode with the keyboard or by clicking it
- **THEN** the application navigates to that mode

#### Scenario: Settings reachable by key
- **WHEN** the user presses the `s` key on the menu
- **THEN** the application opens the Settings screen

#### Scenario: Settings reachable by button
- **WHEN** the user clicks the bottom-left Settings button on the menu
- **THEN** the application opens the Settings screen

#### Scenario: Home key is rebindable
- **WHEN** the user has assigned a Home action (Manage Devices, Use Remote, Settings, or Quit) a custom key and presses it on the menu
- **THEN** the application performs that action, and its default key no longer triggers it

### Requirement: Keyboard control of the remote
The remote SHALL be fully operable from the keyboard, mapping both the arrow keys and the Vim keys `h`, `j`, `k`, and `l` to the D-pad — `h` and Left send LEFT, `j` and Down send DOWN, `k` and Up send UP, `l` and Right send RIGHT — Enter to OK, Backspace to the device's Back key, and the Space bar to the Home key. Escape SHALL leave the remote and return to the previous page rather than sending Back to the device, matching Escape's back-a-page role elsewhere in the application; this leave-the-remote behavior SHALL be the application's Global Go Back action, whose key is customizable via the keyboard-shortcuts capability. The digit keys `0` through `9` SHALL send the matching number key when the active adapter supports it; on an adapter that does not support number keys, pressing a digit SHALL do nothing and SHALL NOT report an error — the hotkey behaves the same as the disabled button. Because `h` now sends the LEFT direction, the Home key SHALL no longer be bound to `h`; the on-screen Home button remains clickable with the mouse. The remaining on-screen buttons (menu, channel, and media transport) are operated by mouse by default and MAY be given a keyboard shortcut via the keyboard-shortcuts capability. While the text field is focused, digit keys and the D-pad letters fill the field rather than sending keys, and Backspace edits the field rather than sending the device's Back key. The device-key mappings described here (D-pad, OK, Back, Home, digits, and Text entry) SHALL be the default shortcuts of rebindable Remote actions that the user MAY change via the keyboard-shortcuts capability.

#### Scenario: Arrow key drives D-pad
- **WHEN** the user presses an arrow key while the remote is focused and no text field is active
- **THEN** the matching directional key is sent

#### Scenario: Vim key drives D-pad
- **WHEN** the user presses `h`, `j`, `k`, or `l` while the remote is focused and no text field is active
- **THEN** LEFT, DOWN, UP, or RIGHT is sent, respectively

#### Scenario: Enter and Backspace mapped
- **WHEN** the user presses Enter or Backspace while the remote is focused and no text field is active
- **THEN** OK or Back is sent to the device, respectively

#### Scenario: Escape leaves the remote
- **WHEN** the user presses Escape while the remote is focused and no text field is active
- **THEN** the remote closes and returns to the previous page, and no Back key is sent to the device

#### Scenario: Backspace edits the focused text field
- **WHEN** the text field is focused and the user presses Backspace
- **THEN** a character is deleted from the field and no Back key is sent to the device

#### Scenario: Space sends Home
- **WHEN** the user presses the Space bar while the remote is focused and no text field is active
- **THEN** the Home key is sent

#### Scenario: Digit key sends number
- **WHEN** the user presses a digit key `0`–`9` while the remote is focused and no text field is active
- **THEN** the matching number key (NUM_0–NUM_9) is sent

#### Scenario: Digit does nothing on an adapter without numbers
- **WHEN** the active adapter does not support number keys and the user presses a digit key while the remote is focused
- **THEN** no key is sent and no error message is shown

#### Scenario: Digits type into the text field
- **WHEN** the text field is focused and the user types digit keys
- **THEN** the digits fill the field and no number key is sent

#### Scenario: Formerly mouse-only key gains a shortcut
- **WHEN** the user assigns a shortcut to a previously unbound remote key (for example Volume Up) and presses it on the remote with a supporting adapter
- **THEN** that device key is sent
