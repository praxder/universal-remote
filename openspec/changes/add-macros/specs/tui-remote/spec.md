## MODIFIED Requirements

### Requirement: On-screen remote surface
The Use Remote mode SHALL present a remote resembling a physical remote with a menu key, a D-pad (up, down, left, right), OK, Back, Home, volume up, volume down, mute, channel up and channel down, the media-transport keys play, pause, play/pause, rewind, and fast-forward and stop, a number pad for the digits 0 through 9, and a row of five custom buttons. The remote's top row SHALL additionally present a Macros control as a fourth button to the right of the menu, Home, and Back buttons, separated from them by a vertical divider marking where the keys sent to the device end and the application's own control begins; activating it SHALL open the macros list (see the macros capability). The Macros control SHALL be reachable by mouse, and MAY be given a keyboard shortcut via the keyboard-shortcuts capability, which activates it identically to a click. Every button MUST be clickable with the mouse. The rewind and fast-forward buttons SHALL use scan-style icons. The remote's buttons SHALL be bordered and sized for comfortable reading, laid out to resemble a physical remote (centered groups, the D-pad as a cross). The five custom buttons SHALL use the same bordered button style as the rest of the remote and SHALL sit in their own centered row. The remote SHALL NOT show an always-visible docked text field; text entry SHALL be reached on demand through a modal opened by the Text action. The remote SHALL size to its content; on a terminal too short to show the full set it SHALL scroll so every button stays reachable rather than clipping.

While a macro recording is in progress, the application SHALL show a recording indicator on the right-hand side of the header bar that names the connected device, and the Macros button SHALL become the control that ends the recording — labelled to stop the recording when the recording captures interactions until stopped, and to cancel when the recording captures a single interaction. The indicator SHALL be short enough that the device's name, type, and IP address remain fully readable beside it at the supported baseline width. Entering the recording state SHALL NOT add any row to the remote, so a remote that fits the supported baseline height without scrolling still fits while recording.

#### Scenario: Remote renders the button set
- **WHEN** the user opens Use Remote for a device
- **THEN** the menu key, D-pad, OK, Back, Home, volume, mute, channel up/down, the media-transport buttons (play, pause, play/pause, rewind, fast-forward, stop), the number pad 0–9, and the row of five custom buttons are shown
- **AND** no docked text field is shown

#### Scenario: Top row offers a Macros control
- **WHEN** the user opens Use Remote for a device
- **THEN** the top row shows a Macros button to the right of the menu, Home, and Back buttons
- **AND** a vertical divider sits between the Back button and the Macros button

#### Scenario: Macros control opens the macros list
- **WHEN** the user clicks the Macros button
- **THEN** the macros list modal opens

#### Scenario: Macros control reachable by an assigned shortcut
- **WHEN** the user has assigned a shortcut to the Macros action and presses it on the remote
- **THEN** the macros list modal opens exactly as if the button had been clicked

#### Scenario: Button click sends action
- **WHEN** the user clicks an enabled remote button
- **THEN** the corresponding key is sent to the selected device

#### Scenario: Recording shows an indicator and an end control
- **WHEN** a macro recording is in progress on the remote
- **THEN** the header bar shows a recording indicator on its right-hand side, still showing the device's name, type, and IP address, and the Macros button is replaced by the control that ends that recording

#### Scenario: Recording adds no rows to the remote
- **WHEN** a macro recording is in progress on a terminal at the supported baseline height
- **THEN** the full remote is still visible without scrolling

#### Scenario: Full remote fits a standard-height terminal
- **WHEN** the user opens Use Remote on a terminal at least the supported baseline height
- **THEN** the full button set is visible without scrolling

#### Scenario: Short terminal scrolls rather than clips
- **WHEN** the terminal is too short to show the full remote
- **THEN** the remote scrolls so every button remains reachable rather than being clipped

### Requirement: Keyboard control of the remote
The remote SHALL be fully operable from the keyboard, mapping both the arrow keys and the Vim keys `h`, `j`, `k`, and `l` to the D-pad — `h` and Left send LEFT, `j` and Down send DOWN, `k` and Up send UP, `l` and Right send RIGHT — Enter to OK, Backspace to the device's Back key, and the Space bar to the Home key. Escape SHALL leave the remote and return to the previous page rather than sending Back to the device, matching Escape's back-a-page role elsewhere in the application; this leave-the-remote behavior SHALL be the application's Global Go Back action, whose key is customizable via the keyboard-shortcuts capability. While a macro recording is in progress the Go Back action SHALL instead cancel that recording and return to the macros list or the macro detail modal it was started from, leaving the remote open and the live session connected; it SHALL NOT leave the remote or send Back to the device. The digit keys `0` through `9` SHALL send the matching number key when the active adapter supports it; on an adapter that does not support number keys, pressing a digit SHALL do nothing and SHALL NOT report an error — the hotkey behaves the same as the disabled button. Because `h` now sends the LEFT direction, the Home key SHALL no longer be bound to `h`; the on-screen Home button remains clickable with the mouse. The remaining on-screen buttons (menu, channel, and media transport) are operated by mouse by default and MAY be given a keyboard shortcut via the keyboard-shortcuts capability. While the text field is focused, digit keys and the D-pad letters fill the field rather than sending keys, and Backspace edits the field rather than sending the device's Back key. The rebindable remote mappings — OK, Back, Home, the digit keys, Text entry, and the twelve formerly mouse-only keys — SHALL be the default shortcuts of rebindable Remote actions that the user MAY change via the keyboard-shortcuts capability. The D-pad directional keys (the arrow keys and `h`/`j`/`k`/`l`) SHALL be reserved for navigation and SHALL NOT be rebindable, though they are listed among the shortcuts for visibility.

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
- **WHEN** the user presses Escape while the remote is focused, no text field is active, and no macro recording is in progress
- **THEN** the remote closes and returns to the previous page, and no Back key is sent to the device

#### Scenario: Go Back cancels a recording instead of leaving the remote
- **WHEN** the user presses the Go Back key while a macro recording is in progress on the remote
- **THEN** the recording is cancelled and the remote stays open with its session connected, and no Back key is sent to the device

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
