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
The Manage Devices mode SHALL present a "Devices" ASCII-art banner, the saved devices, and an always-present add entry as the last row of the list, backed by the device store and exposing add, edit, and delete. When one or more devices are saved, the mode SHALL list the devices first, then a separator, then the add entry; when no devices are saved, the list SHALL show only the add entry. Selecting the add entry — by Enter or by mouse click — SHALL open the add flow. Selecting a device row — by Enter or by mouse click — SHALL open that device for editing. Deleting a device SHALL be triggered by the Backspace key while a device row is highlighted, and SHALL require the user to confirm before the device is removed: the system SHALL present a confirmation prompt naming the device, remove the device only when the user confirms, and leave the store unchanged when the user cancels. The confirmation prompt SHALL default keyboard focus to its cancel action and SHALL let the user move focus between its confirm and cancel actions with the arrow keys. Pressing Backspace while the add entry is highlighted SHALL do nothing. The add and edit screen SHALL present an ASCII-art banner titled "Add Device" when adding and "Edit Device" when editing, styled with the same top and bottom margin as the "Devices" banner. The add and edit screen SHALL order its cells as device type, then name, then IP address. When adding, the device type SHALL be a selector offering the registered platforms by their human-readable names and defaulting to the first; when editing, the device type SHALL be shown as a read-only cell while the name and IP address remain editable. The device-type cell, the name and IP address cells, and the Save button SHALL be reachable both by Tab and by the Up and Down arrow keys — Up moves focus to the previous cell and Down to the next — while the Left and Right arrows continue to move the text cursor within a focused input. Because the Up and Down arrows navigate between cells, the device-type dropdown SHALL open on Enter or Space rather than on an arrow key. The Save button's left edge SHALL be aligned with the cells above it.

#### Scenario: Devices listed above the add row
- **WHEN** the user opens Manage Devices with one or more saved devices
- **THEN** the saved devices are displayed first, followed by a separator, then an add entry as the last row

#### Scenario: First run shows only the add entry
- **WHEN** the user opens Manage Devices with no saved devices
- **THEN** the list shows only the add entry as its single row

#### Scenario: Add entry opens the add flow
- **WHEN** the user selects the add entry by Enter or by mouse click
- **THEN** the application presents the manual entry and confirmation flow and saves the result

#### Scenario: Selecting a device edits it
- **WHEN** the user selects a device row by Enter or by mouse click
- **THEN** the application opens that device in the edit flow

#### Scenario: Backspace prompts for delete confirmation
- **WHEN** the user highlights a saved device row and presses Backspace
- **THEN** the application shows a confirmation prompt naming that device
- **AND** the device is still present in the store while the prompt is open

#### Scenario: Confirming removes the device
- **WHEN** the confirmation prompt is shown and the user confirms the deletion
- **THEN** the device is removed from the store and the list refreshes without it

#### Scenario: Cancelling keeps the device
- **WHEN** the confirmation prompt is shown and the user cancels
- **THEN** no device is removed and the list is unchanged

#### Scenario: Confirmation buttons navigable by arrow keys
- **WHEN** the confirmation prompt is shown and the user presses an arrow key
- **THEN** keyboard focus moves between the confirm and cancel actions

#### Scenario: Backspace on the add entry does nothing
- **WHEN** the add entry is highlighted and the user presses Backspace
- **THEN** no confirmation prompt is shown and no device is removed

#### Scenario: Add and edit screens show an ASCII-art banner
- **WHEN** the user opens the add flow or the edit flow
- **THEN** the screen shows an ASCII-art banner reading "Add Device" or "Edit Device" respectively, with the same top and bottom margin as the "Devices" banner

#### Scenario: Cells ordered device type, name, then IP
- **WHEN** the user opens the add flow or the edit flow
- **THEN** the first cell is the device type, the second is the name, and the third is the IP address

#### Scenario: Device type is read-only when editing
- **WHEN** the user opens the edit flow for a saved device
- **THEN** the device type is shown as a read-only cell that cannot be changed or focused
- **AND** the name and IP address cells remain editable

#### Scenario: Device-type dropdown shows human-readable labels
- **WHEN** the user opens the add flow
- **THEN** the device-type selector lists the registered platforms by their human-readable names rather than their platform identifiers

#### Scenario: Arrow keys move focus between cells
- **WHEN** a cell or the Save button is focused and the user presses the Down arrow
- **THEN** focus moves to the next cell or the Save button
- **AND** pressing the Up arrow moves focus to the previous cell

#### Scenario: Device-type dropdown opens with Enter or Space
- **WHEN** the device-type cell is focused in the add flow and the user presses Enter or Space
- **THEN** the platform dropdown opens for selection

#### Scenario: Save button aligned with the cells
- **WHEN** the user opens the add flow or the edit flow
- **THEN** the Save button's left edge lines up with the left edge of the cells above it

### Requirement: Use Remote entry, selection, and pairing
Entering Use Remote SHALL let the user choose a target device, then connect to it. When the chosen device has no stored credential, the application MUST run pairing first, showing on-screen guidance and allowing the user to cancel. When a credential is already stored, it SHALL connect directly. Whenever the application is connecting to a device — whether directly with a stored credential or after pairing — it SHALL display a modal loading spinner overlaid on the device selection, run the connection off the input handler so the interface stays responsive, and allow the user to cancel the connection while it is in progress. When a connection fails, the application SHALL present an error state that names the device and offers Retry and Back, rather than freezing or crashing; choosing Retry SHALL attempt the connection again and choosing Back SHALL return to device selection. With no saved devices, the mode MUST guide the user toward adding one rather than showing an empty remote. The user MUST be able to leave Use Remote and return to the menu.

#### Scenario: Select among multiple devices
- **WHEN** the user opens Use Remote and more than one device is saved
- **THEN** the application presents the devices for selection before showing a remote

#### Scenario: Pair when no credential
- **WHEN** the chosen device has no stored credential
- **THEN** the application runs pairing with on-screen guidance and, on success, stores the credential and connects, opening the remote

#### Scenario: Pairing cancellable
- **WHEN** the user cancels during pairing
- **THEN** the application returns without opening the remote and without storing a credential

#### Scenario: Connect directly with stored credential
- **WHEN** the chosen device already has a stored credential
- **THEN** the application connects and opens the remote without re-pairing

#### Scenario: Loading spinner shown while connecting
- **WHEN** the application is connecting to the chosen device
- **THEN** a modal loading spinner is shown over the device selection until the connection resolves
- **AND** the interface remains responsive rather than appearing frozen

#### Scenario: Connecting is cancellable
- **WHEN** the user cancels while the connection is in progress
- **THEN** the connect attempt stops and the application returns to device selection without opening a remote

#### Scenario: Connect failure offers retry
- **WHEN** connecting to the chosen device fails
- **THEN** the modal shows an error state naming the device with Retry and Back actions
- **AND** no remote is opened

#### Scenario: Retry re-attempts the connection
- **WHEN** the user chooses Retry after a failed connection
- **THEN** the application attempts to connect to the same device again, showing the loading spinner

#### Scenario: Back after failure returns to selection
- **WHEN** the user chooses Back after a failed connection
- **THEN** the application returns to device selection without opening a remote

#### Scenario: No saved devices
- **WHEN** the user opens Use Remote and no devices are saved
- **THEN** the application guides the user to add a device instead of showing a remote

#### Scenario: Exit back to menu
- **WHEN** the user leaves Use Remote
- **THEN** the application returns to the entry menu

### Requirement: On-screen remote surface
The Use Remote mode SHALL present a remote resembling a physical remote with a D-pad (up, down, left, right), OK, Back, Home, volume up, volume down, mute, and a text field. Every button MUST be clickable with the mouse.

#### Scenario: Remote renders the button set
- **WHEN** the user opens Use Remote for a device
- **THEN** the D-pad, OK, Back, Home, volume, mute, and text field are shown

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

