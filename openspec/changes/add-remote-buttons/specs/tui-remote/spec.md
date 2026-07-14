## MODIFIED Requirements

### Requirement: On-screen remote surface

The Use Remote mode SHALL present a remote resembling a physical remote with a menu key, a D-pad (up, down, left, right), OK, Back, Home, volume up, volume down, mute, channel up and channel down, the media-transport keys play, pause, play/pause, rewind, and fast-forward and stop, a number pad for the digits 0 through 9, and a text field. Every button MUST be clickable with the mouse. The rewind and fast-forward buttons SHALL use scan-style icons. The remote SHALL lay out so that its full button set fits a standard 80×24 terminal without scrolling.

#### Scenario: Remote renders the button set

- **WHEN** the user opens Use Remote for a device
- **THEN** the menu key, D-pad, OK, Back, Home, volume, mute, channel up/down, the media-transport buttons (play, pause, play/pause, rewind, fast-forward, stop), the number pad 0–9, and the text field are shown

#### Scenario: Button click sends action

- **WHEN** the user clicks an enabled remote button
- **THEN** the corresponding key is sent to the selected device

#### Scenario: Full remote fits without scrolling

- **WHEN** the user opens Use Remote on a standard 80×24 terminal
- **THEN** the full button set is visible without scrolling the remote

### Requirement: Keyboard control of the remote

The remote SHALL be fully operable from the keyboard, mapping both the arrow keys and the Vim keys `h`, `j`, `k`, and `l` to the D-pad — `h` and Left send LEFT, `j` and Down send DOWN, `k` and Up send UP, `l` and Right send RIGHT — Enter to OK, Escape to Back, and the Space bar to the Home key. The digit keys `0` through `9` SHALL send the matching number key when the active adapter supports it; on an adapter that does not support number keys, pressing a digit SHALL do nothing and SHALL NOT report an error — the hotkey behaves the same as the disabled button. Because `h` now sends the LEFT direction, the Home key SHALL no longer be bound to `h`; the on-screen Home button remains clickable with the mouse. The remaining on-screen buttons (menu, channel, and media transport) are operated by mouse only. While the text field is focused, digit keys and the D-pad letters fill the field rather than sending keys.

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

#### Scenario: Digit key sends number

- **WHEN** the user presses a digit key `0`–`9` while the remote is focused and no text field is active
- **THEN** the matching number key (NUM_0–NUM_9) is sent

#### Scenario: Digit does nothing on an adapter without numbers

- **WHEN** the active adapter does not support number keys and the user presses a digit key while the remote is focused
- **THEN** no key is sent and no error message is shown

#### Scenario: Digits type into the text field

- **WHEN** the text field is focused and the user types digit keys
- **THEN** the digits fill the field and no number key is sent
