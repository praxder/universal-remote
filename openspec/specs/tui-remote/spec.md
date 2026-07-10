# tui-remote Specification

## Purpose
TBD - created by archiving change scaffold-samsung-remote. Update Purpose after archive.
## Requirements
### Requirement: Menu-driven entry with two modes
The application SHALL launch into a menu offering two modes: Manage Devices and Use Remote. Both modes MUST be reachable by keyboard and by mouse.

#### Scenario: Menu offers both modes
- **WHEN** the application starts
- **THEN** it shows a menu with Manage Devices and Use Remote options

#### Scenario: Mode reachable by keyboard and mouse
- **WHEN** the user selects a mode with the keyboard or by clicking it
- **THEN** the application navigates to that mode

### Requirement: Device management screens
The Manage Devices mode SHALL present the saved devices and expose add, edit, and delete actions backed by the device store.

#### Scenario: Devices listed
- **WHEN** the user opens Manage Devices
- **THEN** the saved devices are displayed

#### Scenario: Add flow reachable
- **WHEN** the user chooses to add a device
- **THEN** the application presents the IP-entry and confirmation flow and saves the result

### Requirement: Use Remote entry, selection, and pairing
Entering Use Remote SHALL let the user choose a target device, then connect to it. When the chosen device has no stored credential, the application MUST run pairing first, showing on-screen guidance and allowing the user to cancel. When a credential is already stored, it SHALL connect directly. With no saved devices, the mode MUST guide the user toward adding one rather than showing an empty remote. The user MUST be able to leave Use Remote and return to the menu.

#### Scenario: Select among multiple devices
- **WHEN** the user opens Use Remote and more than one device is saved
- **THEN** the application presents the devices for selection before showing a remote

#### Scenario: Pair when no credential
- **WHEN** the chosen device has no stored credential
- **THEN** the application runs pairing with on-screen guidance and, on success, stores the credential and opens the remote

#### Scenario: Pairing cancellable
- **WHEN** the user cancels during pairing
- **THEN** the application returns without opening the remote and without storing a credential

#### Scenario: Connect directly with stored credential
- **WHEN** the chosen device already has a stored credential
- **THEN** the application connects and opens the remote without re-pairing

#### Scenario: No saved devices
- **WHEN** the user opens Use Remote and no devices are saved
- **THEN** the application guides the user to add a device instead of showing a remote

#### Scenario: Exit back to menu
- **WHEN** the user leaves Use Remote
- **THEN** the application returns to the entry menu

### Requirement: On-screen remote surface
The Use Remote mode SHALL present a remote resembling a physical remote with a D-pad (up, down, left, right), OK, Back, Home, volume up, volume down, mute, power, and a text field. Every button MUST be clickable with the mouse.

#### Scenario: Remote renders the button set
- **WHEN** the user opens Use Remote for a device
- **THEN** the D-pad, OK, Back, Home, volume, mute, power, and text field are shown

#### Scenario: Button click sends action
- **WHEN** the user clicks a remote button
- **THEN** the corresponding key is sent to the selected device

### Requirement: Keyboard control of the remote
The remote SHALL be fully operable from the keyboard, mapping arrow keys to the D-pad, Enter to OK, Escape to Back, and Home to the home key.

#### Scenario: Arrow key drives D-pad
- **WHEN** the user presses an arrow key while the remote is focused and no text field is active
- **THEN** the matching directional key is sent

#### Scenario: Enter and Escape mapped
- **WHEN** the user presses Enter or Escape while the remote is focused and no text field is active
- **THEN** OK or Back is sent, respectively

### Requirement: Capability-driven button state
The remote SHALL disable and visibly indicate any button whose key the active device's adapter does not declare as supported.

#### Scenario: Unsupported button disabled
- **WHEN** the active adapter does not declare support for a key
- **THEN** that button is shown in a disabled state and does not send an action when activated

### Requirement: Text-entry focus behavior
The remote's text field SHALL define a text-entry mode: while the field is focused, typed characters fill a buffer and Enter sends the buffered text; Escape exits the field without sending Back. When text is unsupported by the active adapter, the field MUST be disabled with a clear message.

#### Scenario: Compose then send
- **WHEN** the text field is focused and the user types characters and presses Enter
- **THEN** the buffered text is sent to the device as a single text action

#### Scenario: Escape exits field, not Back
- **WHEN** the text field is focused and the user presses Escape
- **THEN** focus leaves the field and no Back key is sent

#### Scenario: Text unsupported disables field
- **WHEN** the active adapter reports text as unsupported
- **THEN** the text field is disabled and a message explains text is not supported on this device

### Requirement: Landing menu shows a movie/TV quote
The entry menu SHALL display one famous movie or TV quote with attribution beneath the two mode buttons. The attribution SHALL read `— <character>, <source>`. A quote provider selects the quote once per launch. When no quote is available, the menu MUST render without a quote row and MUST NOT fail.

#### Scenario: Quote shown beneath the mode buttons
- **WHEN** the application starts and a quote is available
- **THEN** the menu displays the quote text with an attribution reading `— <character>, <source>` beneath the Manage Devices and Use Remote buttons

#### Scenario: No quote available
- **WHEN** the application starts and no quote is available
- **THEN** the menu renders the mode buttons without a quote row and does not fail

#### Scenario: Quote chosen once per launch
- **WHEN** the menu is shown for the current session
- **THEN** the quote provider is consulted once and the same quote remains for that session

