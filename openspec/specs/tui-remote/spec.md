# tui-remote Specification

## Purpose
The Textual terminal UI: the entry menu, device management, network discovery, and the on-screen remote, covering device selection, pairing, connection, reachability indicators, text entry, and custom buttons.
## Requirements
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

### Requirement: Device management screens
The Manage Devices mode SHALL present a "Devices" ASCII-art banner, the saved devices, and an always-present add entry as the last row of the list, backed by the device store and exposing add, edit, and delete. When one or more devices are saved, the mode SHALL list the devices first, then a separator, then the add entry; when no devices are saved, the list SHALL show only the add entry. Selecting the add entry — by Enter or by mouse click — SHALL open device discovery (see the "Add device via discovery" requirement). Selecting a device row — by Enter or by mouse click — SHALL open that device for editing. Deleting a device SHALL be triggered either by the Backspace key while a device row is highlighted on the list, or by a Delete button on the edit screen (shown only when editing a device, never when adding), and SHALL require the user to confirm before the device is removed: the system SHALL present the same confirmation prompt naming the device, remove the device only when the user confirms, and leave the store unchanged when the user cancels. When deletion is confirmed from the edit screen, the application SHALL return to the saved-device list, which SHALL no longer show the removed device. The confirmation prompt SHALL default keyboard focus to its cancel action and SHALL let the user move focus between its confirm and cancel actions with the arrow keys. Pressing Backspace while the add entry is highlighted SHALL do nothing. The add and edit screen SHALL present an ASCII-art banner titled "Add Device" when adding and "Edit Device" when editing, styled with the same top and bottom margin as the "Devices" banner. The add and edit screen SHALL order its cells as device type, then name, then IP address. When adding, the device type SHALL be a selector offering the registered platforms by their human-readable names and defaulting to the first; when editing, the device type SHALL be shown as a read-only cell while the name and IP address remain editable. When editing, the screen SHALL show a Delete button below Save, aligned to the same left edge; the add screen SHALL NOT show a Delete button. The device-type cell, the name and IP address cells, the Save button, and — when editing — the Delete button SHALL be reachable both by Tab and by the Up and Down arrow keys — Up moves focus to the previous cell and Down to the next — while the Left and Right arrows continue to move the text cursor within a focused input. Because the Up and Down arrows navigate between cells, the device-type dropdown SHALL open on Enter or Space rather than on an arrow key. The Save button's left edge SHALL be aligned with the cells above it.

#### Scenario: Devices listed above the add row
- **WHEN** the user opens Manage Devices with one or more saved devices
- **THEN** the saved devices are displayed first, followed by a separator, then an add entry as the last row

#### Scenario: First run shows only the add entry
- **WHEN** the user opens Manage Devices with no saved devices
- **THEN** the list shows only the add entry as its single row

#### Scenario: Add entry opens device discovery
- **WHEN** the user selects the add entry by Enter or by mouse click
- **THEN** the application opens the device discovery screen and a scan begins

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

#### Scenario: Edit screen offers a Delete button
- **WHEN** the user opens the edit flow for a saved device
- **THEN** a Delete button is shown below the Save button

#### Scenario: Delete button prompts for the same confirmation
- **WHEN** the user activates the Delete button on the edit screen
- **THEN** the application shows the same delete-confirmation prompt naming that device
- **AND** the device is still present in the store while the prompt is open

#### Scenario: Confirming delete from the edit screen returns to the list
- **WHEN** the delete confirmation raised from the edit screen is confirmed
- **THEN** the device is removed from the store
- **AND** the application returns to the saved-device list, which no longer shows the removed device

#### Scenario: Cancelling delete from the edit screen keeps the device
- **WHEN** the delete confirmation raised from the edit screen is cancelled
- **THEN** no device is removed and the user remains on the edit screen

#### Scenario: Add screen has no Delete button
- **WHEN** the user opens the add flow
- **THEN** no Delete button is shown

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
Entering Use Remote SHALL let the user choose a target device, then connect to it. When the chosen device has no stored credential and its adapter requires pairing, the application MUST run pairing first, presenting the on-screen guidance as a modal overlaid on the device selection and allowing the user to cancel. When the chosen device's adapter declares that it requires no pairing, the application SHALL connect directly without running pairing, even when no credential is stored. When an adapter requests a value during pairing — such as a PIN the device displays on screen — the application SHALL present that request within the same pairing modal, with the adapter-supplied message and a text input, pass the entered value back to the adapter to continue pairing, and allow the user to cancel while the prompt is shown. Pairing guidance SHALL reflect the adapter's flow rather than assuming a single pairing style. When a credential is already stored, it SHALL connect directly. Whenever the application is connecting to a device — whether directly with a stored credential, directly for a no-pairing adapter, or after pairing — it SHALL display a modal loading spinner overlaid on the device selection, run the connection off the input handler so the interface stays responsive, and allow the user to cancel the connection while it is in progress. When a connection fails, the application SHALL present an error state that names the device and offers Retry and Back, rather than freezing or crashing; choosing Retry SHALL attempt the connection again and choosing Back SHALL return to device selection. With no saved devices, the mode MUST guide the user toward adding one rather than showing an empty remote. The user MUST be able to leave Use Remote and return to the menu.

#### Scenario: Select among multiple devices
- **WHEN** the user opens Use Remote and more than one device is saved
- **THEN** the application presents the devices for selection before showing a remote

#### Scenario: Pair when no credential
- **WHEN** the chosen device has no stored credential and its adapter requires pairing
- **THEN** the application runs pairing with on-screen guidance and, on success, stores the credential and connects, opening the remote

#### Scenario: Skip pairing when the adapter needs none
- **WHEN** the chosen device's adapter declares it requires no pairing
- **THEN** the application connects directly and opens the remote without running pairing, even though no credential is stored

#### Scenario: Pairing shown as a modal overlay
- **WHEN** the application runs pairing for the chosen device
- **THEN** the pairing guidance is presented as a modal overlaid on the device selection, dimming it behind the dialog rather than replacing the screen
- **AND** both the initial guidance state and any adapter value prompt appear within that same modal

#### Scenario: Adapter requests a value during pairing
- **WHEN** the adapter requests a value during pairing, supplying a message such as a prompt to enter the PIN shown on the device
- **THEN** the application shows that message with a text input
- **AND** the entered value is passed back to the adapter so pairing continues, storing the credential on success

#### Scenario: Value prompt cancellable
- **WHEN** the user cancels while a pairing value prompt is shown
- **THEN** the application returns without opening the remote and without storing a credential

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
The Use Remote mode SHALL present a remote resembling a physical remote with a menu key, a D-pad (up, down, left, right), OK, Back, Home, volume up, volume down, mute, channel up and channel down, the media-transport keys play, pause, play/pause, rewind, and fast-forward and stop, a number pad for the digits 0 through 9, and a row of five custom buttons. Every button MUST be clickable with the mouse. The rewind and fast-forward buttons SHALL use scan-style icons. The remote's buttons SHALL be bordered and sized for comfortable reading, laid out to resemble a physical remote (centered groups, the D-pad as a cross). The five custom buttons SHALL use the same bordered button style as the rest of the remote and SHALL sit in their own centered row. The remote SHALL NOT show an always-visible docked text field; text entry SHALL be reached on demand through a modal opened by the Text action. The remote SHALL size to its content; on a terminal too short to show the full set it SHALL scroll so every button stays reachable rather than clipping.

#### Scenario: Remote renders the button set
- **WHEN** the user opens Use Remote for a device
- **THEN** the menu key, D-pad, OK, Back, Home, volume, mute, channel up/down, the media-transport buttons (play, pause, play/pause, rewind, fast-forward, stop), the number pad 0–9, and the row of five custom buttons are shown
- **AND** no docked text field is shown

#### Scenario: Button click sends action
- **WHEN** the user clicks an enabled remote button
- **THEN** the corresponding key is sent to the selected device

#### Scenario: Full remote fits a standard-height terminal
- **WHEN** the user opens Use Remote on a terminal at least the supported baseline height
- **THEN** the full button set is visible without scrolling

#### Scenario: Short terminal scrolls rather than clips
- **WHEN** the terminal is too short to show the full remote
- **THEN** the remote scrolls so every button remains reachable rather than being clipped

### Requirement: Keyboard control of the remote
The remote SHALL be fully operable from the keyboard, mapping both the arrow keys and the Vim keys `h`, `j`, `k`, and `l` to the D-pad — `h` and Left send LEFT, `j` and Down send DOWN, `k` and Up send UP, `l` and Right send RIGHT — Enter to OK, Backspace to the device's Back key, and the Space bar to the Home key. Escape SHALL leave the remote and return to the previous page rather than sending Back to the device, matching Escape's back-a-page role elsewhere in the application; this leave-the-remote behavior SHALL be the application's Global Go Back action, whose key is customizable via the keyboard-shortcuts capability. The digit keys `0` through `9` SHALL send the matching number key when the active adapter supports it; on an adapter that does not support number keys, pressing a digit SHALL do nothing and SHALL NOT report an error — the hotkey behaves the same as the disabled button. Because `h` now sends the LEFT direction, the Home key SHALL no longer be bound to `h`; the on-screen Home button remains clickable with the mouse. The remaining on-screen buttons (menu, channel, and media transport) are operated by mouse by default and MAY be given a keyboard shortcut via the keyboard-shortcuts capability. While the text field is focused, digit keys and the D-pad letters fill the field rather than sending keys, and Backspace edits the field rather than sending the device's Back key. The rebindable remote mappings — OK, Back, Home, the digit keys, Text entry, and the twelve formerly mouse-only keys — SHALL be the default shortcuts of rebindable Remote actions that the user MAY change via the keyboard-shortcuts capability. The D-pad directional keys (the arrow keys and `h`/`j`/`k`/`l`) SHALL be reserved for navigation and SHALL NOT be rebindable, though they are listed among the shortcuts for visibility.

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

### Requirement: Capability-driven button state
The remote SHALL disable and visibly indicate any button whose key the active device's adapter does not declare as supported.

#### Scenario: Unsupported button disabled
- **WHEN** the active adapter does not declare support for a key
- **THEN** that button is shown in a disabled state and does not send an action when activated

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

### Requirement: Reachability indicator in the Use Remote picker
The Use Remote device picker SHALL display a reachability indicator next to each saved device, positioned before the device's 1-based position number: green when the device is reachable, red when unreachable, and yellow when the status is unknown or has not yet been determined. The picker SHALL show every device immediately with a yellow (unknown) indicator, then determine each device's reachability without blocking selection, updating each indicator in place as its status resolves. The picker SHALL refresh reachability on a recurring interval while it is open and SHALL stop probing when the user leaves the screen. The indicator SHALL be advisory only: the user MAY select and connect to any device regardless of its indicator, including one shown as unreachable.

#### Scenario: Devices shown immediately as unknown
- **WHEN** the user opens Use Remote with one or more saved devices
- **THEN** each device is listed right away with a yellow indicator before its position number
- **AND** the list is usable before any reachability result has resolved

#### Scenario: Reachable device turns green
- **WHEN** a device's reachability resolves to reachable
- **THEN** that device's indicator updates in place to green

#### Scenario: Unreachable device turns red
- **WHEN** a device's reachability resolves to unreachable
- **THEN** that device's indicator updates in place to red

#### Scenario: Indicators refresh on an interval
- **WHEN** the picker has been open for the refresh interval
- **THEN** the picker re-probes the devices and updates each indicator to its current status

#### Scenario: Probing stops on leaving the screen
- **WHEN** the user leaves the Use Remote picker
- **THEN** no further reachability probes are started

#### Scenario: Unreachable device remains selectable
- **WHEN** a device shown with a red indicator is selected
- **THEN** the application begins the connect/pair flow for it exactly as for any other device

### Requirement: Add device via discovery
The Manage Devices add entry SHALL open a device discovery screen that lists devices discovered on the local network — each row showing the device's name, its human-readable platform, and its IP address — and presents "+ Add manually" as the last row. The screen SHALL indicate while a scan is in progress and SHALL populate discovered rows as scans answer rather than waiting for all scans to finish. The "+ Add manually" row SHALL be present and selectable before the scan completes, and selecting it SHALL open the existing manual add flow. Selecting a discovered row SHALL save that device to the store — without manual entry and without pairing — persisting its name, platform, IP address, and any adapter-provided reconnection identifier, then return to the saved-device list. The screen SHALL be dismissible, returning to the saved-device list, while a scan is still in progress.

#### Scenario: Discovered device shows name, type, and IP
- **WHEN** a device has been discovered
- **THEN** its row shows the device name, its human-readable platform, and its IP address

#### Scenario: Rows stream in during the scan
- **WHEN** a scan is in progress and a device is discovered
- **THEN** its row appears without waiting for the scan to finish

#### Scenario: Manual entry is available before the scan finishes
- **WHEN** the discovery screen is shown and the scan has not finished
- **THEN** "+ Add manually" is present as the last row and is selectable

#### Scenario: Manual row opens the manual add flow
- **WHEN** the user selects "+ Add manually"
- **THEN** the existing manual entry and confirmation flow opens

#### Scenario: Selecting a discovered device adds it
- **WHEN** the user selects a discovered row
- **THEN** the device is saved to the store with its name, platform, and IP address, and its reconnection identifier when the scan provided one
- **AND** the screen returns to the saved-device list showing the newly added device

#### Scenario: Screen is dismissible while scanning
- **WHEN** a scan is in progress and the user dismisses the discovery screen
- **THEN** the application returns to the saved-device list without error

### Requirement: Command palette contents
The application's command palette (opened with Ctrl+P) SHALL expose the Theme, Quit, and Keys commands inherited from Textual plus the application's own "Keyboard Shortcuts" command (a read-only shortcuts view; see the keyboard-shortcuts capability), and SHALL NOT expose the Maximize command or the Screenshot command. Because nothing in the application maximizes a widget, the Minimize command — shown by Textual only while a widget is maximized — SHALL likewise never appear.

#### Scenario: Palette lists the retained commands
- **WHEN** the user opens the command palette
- **THEN** its commands are Theme, Quit, Keys, and Keyboard Shortcuts

#### Scenario: Maximize is excluded
- **WHEN** the user opens the command palette
- **THEN** no Maximize command is listed

#### Scenario: Screenshot is excluded
- **WHEN** the user opens the command palette
- **THEN** no Screenshot command is listed

### Requirement: Android TV text-input mode toggle

The Add Device and Edit Device screens SHALL present a text-input-mode toggle **only when the device's type is Android TV**; for every other device type the toggle SHALL NOT appear, and the device list SHALL NOT offer any action to change a device's text-input mode. The toggle selects between standard Remote v2 text and ADB text.

When the user switches the toggle to ADB, the application SHALL run the one-time ADB pairing, prompting for the pairing address and pairing code and pairing through the adapter. On success the device SHALL be recorded as opted into ADB text when the form is saved. On cancel or failure the toggle SHALL revert to standard and the device SHALL NOT be opted in. Switching the toggle back to standard SHALL clear the opt-in without pairing.

#### Scenario: Toggle appears only for Android TV

- **WHEN** the Add or Edit screen is shown for an Android TV device
- **THEN** the text-input-mode toggle is visible
- **AND WHEN** the screen is shown for a device of any other type
- **THEN** the toggle is not shown

#### Scenario: Switching to ADB pairs and opts in on save

- **WHEN** the user switches the toggle to ADB, completes pairing with a valid address and code, and saves the form
- **THEN** the application records the device as opted into ADB text and persists it

#### Scenario: Failed or cancelled pairing reverts the toggle

- **WHEN** the user switches the toggle to ADB but the pairing is cancelled or fails
- **THEN** the toggle reverts to standard and the device is not opted into ADB text

#### Scenario: Editing flips an existing device's mode

- **WHEN** the user edits an Android TV device already opted into ADB text and switches the toggle back to standard, then saves
- **THEN** the device is no longer opted into ADB text and no pairing is run

### Requirement: Post-add ADB text hint for Android TV

When an Android TV device is added directly from the discovery screen, the application SHALL show a one-time hint that text input can be routed over ADB if it has trouble in some apps, pointing the user to edit the device and switch its text-input mode. The hint SHALL NOT appear when a device of any other type is added.

#### Scenario: Adding a discovered Android TV device shows the hint

- **WHEN** the user selects and adds an Android TV device from the discovery screen
- **THEN** the application shows a hint that text input can be switched to ADB, which the user dismisses

#### Scenario: Adding a non-Android device shows no hint

- **WHEN** the user selects and adds a device of any other type from the discovery screen
- **THEN** no ADB text hint is shown

### Requirement: ADB text unavailable is surfaced during use

When a device is opted into ADB text and a text send falls back to Remote v2 because the ADB path was unavailable, the Use Remote surface SHALL show a one-line status explaining that ADB text was unavailable, rather than failing silently or blocking further use.

#### Scenario: Fallback shows a status message

- **WHEN** an opted-in device's text send falls back to Remote v2 because the ADB path was unavailable
- **THEN** the remote shows a one-line status explaining that ADB text was unavailable

### Requirement: Remote screen status bar identifies the active device
While Use Remote mode is showing the on-screen remote, the top status bar SHALL identify the active device as `Name: <name> • Type: <type> • IP: <ip>`, where `<name>` is the device's name, `<ip>` is its IP address, and `<type>` is the platform's human-readable label — the same label used for the device-type picker on the add/edit screen, not the raw platform identifier. The status bar SHALL NOT include any other prefix or text.

#### Scenario: Status bar shows name, type, and IP
- **WHEN** the user opens Use Remote for a device named "Living Room TV" on the `androidtv` platform (human-readable label "Android TV") at IP 192.168.20.51
- **THEN** the status bar reads `Name: Living Room TV • Type: Android TV • IP: 192.168.20.51`

#### Scenario: Type uses the human-readable label
- **WHEN** the remote is shown for a device
- **THEN** the status bar's Type field displays the platform's human-readable label rather than the raw platform identifier

### Requirement: Text entry via a modal
The remote's Text action SHALL open a text-entry modal rather than focusing a docked field. While the modal's input is focused, typed characters fill a buffer and Enter sends the buffered text as a single text action and closes the modal; Escape closes the modal without sending the buffered text and without sending the device's Back key. When text is unsupported by the active adapter, activating the Text action SHALL surface a clear message that text is not supported on this device and SHALL NOT open an editable input.

#### Scenario: Compose then send
- **WHEN** the text-entry modal is open and the user types characters and presses Enter
- **THEN** the buffered text is sent to the device as a single text action and the modal closes

#### Scenario: Escape closes the modal, not Back
- **WHEN** the text-entry modal is open and the user presses Escape
- **THEN** the modal closes, no buffered text is sent, and no Back key is sent to the device

#### Scenario: Text unsupported surfaces a message
- **WHEN** the active adapter reports text as unsupported and the user activates the Text action
- **THEN** a message explains text is not supported on this device and no editable text input is opened

### Requirement: Custom buttons on the remote
The remote SHALL present exactly five custom buttons in a dedicated row. Each button SHALL show its configured title resolved for the active device, or its default title `Custom N` (where `N` is the button's 1-based position) when no title is configured for that device. Each custom button MUST be clickable with the mouse. Clicking a custom button SHALL run its assigned action when one is resolved for the active device, and SHALL open the button's configuration modal when no action is assigned. A custom button MAY also be activated by an assigned keyboard shortcut (see the keyboard-shortcuts catalog), which SHALL behave identically to clicking that button — running its resolved action, or opening its configuration when none is assigned. To re-edit a button that has an assigned action, the user SHALL use a distinct edit gesture: pressing an edit-mode key SHALL arm edit-mode, and the next activation of a custom button — whether by clicking it or by pressing its keyboard shortcut — SHALL open that button's configuration modal instead of running its action, after which edit-mode SHALL clear. The edit-mode key SHALL toggle: pressing it while edit-mode is already armed SHALL disarm edit-mode without opening any configuration. While edit-mode is armed, the custom buttons SHALL show a visual indicator distinguishing the armed edit state from their normal run appearance, and that indicator SHALL clear together with edit-mode.

#### Scenario: Custom buttons show defaults when unconfigured
- **WHEN** the user opens Use Remote for a device with no custom-button titles saved
- **THEN** the five custom buttons read `Custom 1`, `Custom 2`, `Custom 3`, `Custom 4`, and `Custom 5`

#### Scenario: Custom button shows its resolved title
- **WHEN** a custom button has a title configured that applies to the active device
- **THEN** that button shows the configured title instead of its `Custom N` default

#### Scenario: Clicking a button with no action opens its configuration
- **WHEN** the user clicks a custom button that has no assigned action for the active device
- **THEN** the Button Config modal for that button opens

#### Scenario: Clicking a button with an action runs it
- **WHEN** the user clicks a custom button that has an assigned action for the active device
- **THEN** that action runs and the configuration modal does not open

#### Scenario: Edit gesture opens configuration for a configured button
- **WHEN** the user presses the edit-mode key and then activates a custom button that has an assigned action
- **THEN** the Button Config modal for that button opens instead of running the action, and edit-mode clears

#### Scenario: Edit-mode shows a visual indicator
- **WHEN** the user presses the edit-mode key to arm edit-mode
- **THEN** the custom buttons show an armed indicator that distinguishes edit-mode from their normal appearance, and the indicator clears once a custom button is activated and edit-mode ends

#### Scenario: Pressing the edit-mode key again disarms edit-mode
- **WHEN** the user presses the edit-mode key while edit-mode is already armed
- **THEN** edit-mode disarms without opening any configuration and the armed indicator clears

#### Scenario: A keyboard shortcut activates a custom button
- **WHEN** the user has assigned a shortcut to a custom button and presses it on the remote
- **THEN** the same thing happens as clicking that button — its resolved action runs, or its configuration opens when no action is assigned

### Requirement: Custom button configuration modal
The Button Config modal's heading SHALL be the static text "Configure Custom Button". The modal SHALL contain a button-title text input, a three-way scope selector offering This Device, Device Type, and Global, an Action Type control, and OK, Cancel, and Reset controls. The Action Type control SHALL be active: selecting it SHALL open the Action Type list, from which choosing an action type opens that action type's configuration and, on completion, assigns the action to the button at the selected scope. Selecting OK SHALL save the entered title and any assigned action for the button at the selected scope, persist them, and update the button on the remote to show the newly resolved title and resize to fit it immediately, without requiring the remote to be reopened. So the selected scope is the one that resolves, saving SHALL also drop the button's entry at any scope more specific than the selected scope for the active device and its type, leaving scopes less specific than the selected one untouched. Selecting Cancel SHALL close the modal without changing any saved title or action. Selecting Reset SHALL clear the button's title and action at every scope for the active device — the device, its device type, and global — returning it to its default title with no action, persist that, close the modal, and update the button on the remote to its default. When opened, the scope selector SHALL preselect the scope the button's shown title resolves from — the specific device, then device type, then global — so reopening the modal reflects where the title is actually stored; when no title is configured at any scope it SHALL default to This Device.

#### Scenario: Save a title for this device
- **WHEN** the user opens a custom button's config modal, enters a title, leaves the scope on This Device, and selects OK
- **THEN** the modal closes and that button on the remote shows the entered title for the current device

#### Scenario: Save a title for the device type
- **WHEN** the user enters a title, sets the scope to Device Type, and selects OK
- **THEN** the title is saved for the current device's type and the button shows it

#### Scenario: Save a title globally
- **WHEN** the user enters a title, sets the scope to Global, and selects OK
- **THEN** the title is saved for the button regardless of device or device type and the button shows it

#### Scenario: Switching to a broader scope takes effect
- **WHEN** a button whose title is stored at This Device is reopened, its scope is changed to Global, and OK is selected
- **THEN** the more-specific device entry is cleared for the active device and the button shows the Global title rather than the old device title

#### Scenario: Reset returns a button to its default
- **WHEN** the user opens a configured button's config modal and selects Reset
- **THEN** the modal closes and the button reads its default `Custom N` title with no action, at every scope for the active device

#### Scenario: Cancel discards changes
- **WHEN** the user opens a custom button's config modal, edits the title, and selects Cancel
- **THEN** the modal closes and the button's saved title and action are unchanged

#### Scenario: Action Type opens the action list
- **WHEN** the user selects the Action Type control in the Button Config modal
- **THEN** the Action Type list opens for choosing an action type

#### Scenario: Heading is static text
- **WHEN** the user opens any custom button's config modal
- **THEN** the heading reads "Configure Custom Button" regardless of which button was opened

#### Scenario: Scope selector reflects where the title is stored
- **WHEN** a button's title was saved at the Global scope and the user reopens its config modal
- **THEN** the scope selector shows Global selected rather than This Device

#### Scenario: Saved title resizes the button immediately
- **WHEN** the user saves a title that is longer or shorter than the current one
- **THEN** the button on the remote shows the new title and its width adjusts to fit immediately, without reopening the remote

