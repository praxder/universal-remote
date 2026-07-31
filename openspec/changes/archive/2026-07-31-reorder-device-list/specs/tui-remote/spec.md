## MODIFIED Requirements

### Requirement: Device management screens
The Manage Devices mode SHALL present a "Devices" ASCII-art banner, the saved devices, and an always-present add entry as the last row of the list, backed by the device store and exposing add, edit, delete, and reorder. When one or more devices are saved, the mode SHALL list the devices first, then a separator, then the add entry; when no devices are saved, the list SHALL show only the add entry. Selecting the add entry — by Enter or by mouse click — SHALL open device discovery (see the "Add device via discovery" requirement). Selecting a device row — by Enter or by mouse click — SHALL open that device for editing. Deleting a device SHALL be triggered either by the Backspace key while a device row is highlighted on the list, or by a Delete button on the edit screen (shown only when editing a device, never when adding), and SHALL require the user to confirm before the device is removed: the system SHALL present the same confirmation prompt naming the device, remove the device only when the user confirms, and leave the store unchanged when the user cancels. When deletion is confirmed from the edit screen, the application SHALL return to the saved-device list, which SHALL no longer show the removed device. The confirmation prompt SHALL default keyboard focus to its cancel action and SHALL let the user move focus between its confirm and cancel actions with the arrow keys. Pressing Backspace while the add entry is highlighted SHALL do nothing.

Below the device list — outside it, after the add entry — the mode SHALL present a Move Up button and a Move Down button side by side on one row, which move the highlighted device one place earlier or one place later in the saved-device order (see the device-management capability's "Reorder saved devices" requirement). The same two moves SHALL also be available from the list itself by `shift+up` and `shift+down`, and — mirroring this application's Vim navigation aliases — by `K` and `J`, so a keyboard user need not leave the list; the plain Up and Down arrows and the unshifted Vim keys continue to move the highlight without reordering. A move SHALL persist immediately and SHALL NOT change any stored field of the device. After a move the list SHALL renumber its rows and SHALL keep the moved device highlighted at its new position, so pressing the same move again walks that device a further place. Activating a move by mouse or by Tab-and-Enter SHALL return keyboard focus to the device list. The two buttons SHALL be present and enabled whenever the mode is shown, and a move that cannot be made SHALL do nothing at all — leaving the list and the store unchanged — in each of these cases: the highlighted device is already first and Move Up is activated; the highlighted device is already last and Move Down is activated; the add entry is highlighted; fewer than two devices are saved. Reordering SHALL be offered only here: no other screen SHALL change the device order.

The add and edit screen SHALL present an ASCII-art banner titled "Add Device" when adding and "Edit Device" when editing, styled with the same top and bottom margin as the "Devices" banner. The add and edit screen SHALL order its cells as device type, then name, then IP address. When adding, the device type SHALL be a selector offering the registered platforms by their human-readable names and defaulting to the first; when editing, the device type SHALL be shown as a read-only cell while the name and IP address remain editable. When editing, the screen SHALL show a Delete button below Save, aligned to the same left edge; the add screen SHALL NOT show a Delete button. The device-type cell, the name and IP address cells, the Save button, and — when editing — the Delete button SHALL be reachable both by Tab and by the Up and Down arrow keys — Up moves focus to the previous cell and Down to the next — while the Left and Right arrows continue to move the text cursor within a focused input. Because the Up and Down arrows navigate between cells, the device-type dropdown SHALL open on Enter or Space rather than on an arrow key. The Save button's left edge SHALL be aligned with the cells above it.

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

#### Scenario: Move buttons shown below the list
- **WHEN** the user opens Manage Devices
- **THEN** a Move Up button and a Move Down button are shown side by side on one row below the list, both enabled

#### Scenario: Move Down button moves the highlighted device later
- **WHEN** the first device is highlighted and the user activates Move Down
- **THEN** that device is listed second, the previously second device is listed first, and the rows are renumbered accordingly
- **AND** the new order is persisted to the store

#### Scenario: Move Up button moves the highlighted device earlier
- **WHEN** the second device is highlighted and the user activates Move Up
- **THEN** that device is listed first and the rows are renumbered accordingly
- **AND** the new order is persisted to the store

#### Scenario: Shift-arrow keys move the highlighted device
- **WHEN** a device row is highlighted and the user presses `shift+down` or `shift+up`
- **THEN** that device moves one place later or one place earlier, exactly as the matching button does

#### Scenario: Shifted Vim keys move the highlighted device
- **WHEN** a device row is highlighted and the user presses `J` or `K`
- **THEN** that device moves one place later or one place earlier, the same as `shift+down` or `shift+up`

#### Scenario: Highlight follows the moved device
- **WHEN** the first of three devices is highlighted and the user moves it down twice
- **THEN** that device is listed third and is the highlighted row

#### Scenario: Focus returns to the list after a button move
- **WHEN** the user activates Move Up or Move Down from the button
- **THEN** keyboard focus is on the device list, with the moved device highlighted

#### Scenario: Moving the first device up does nothing
- **WHEN** the first device is highlighted and the user activates Move Up
- **THEN** the listed order is unchanged and the store is unchanged

#### Scenario: Moving the last device down does nothing
- **WHEN** the last device is highlighted and the user activates Move Down
- **THEN** the listed order is unchanged and the store is unchanged

#### Scenario: Moving with the add entry highlighted does nothing
- **WHEN** the add entry is highlighted and the user activates either move
- **THEN** the listed order is unchanged and the store is unchanged

#### Scenario: A move leaves the device's stored fields alone
- **WHEN** a device is moved on the list
- **THEN** its stored name, platform, and IP address are unchanged

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

### Requirement: Numbered device lists and digit selection
Both device-selection lists — the Manage Devices list and the Use Remote device picker — SHALL prefix each saved device row with its 1-based position followed by a period and a space (for example, `1. Apple TV`, `2. Android TV`). The numbering SHALL reflect the stored device order, which the user controls from the Manage Devices list (see the "Device management screens" requirement) and which persists across runs; both lists SHALL show the same order, and the Use Remote picker SHALL reflect a reordering made on the Manage Devices list the next time it is opened. The numbering SHALL count only saved devices; the `+ Add` entry SHALL NOT be numbered. Pressing a digit key `1` through `9` while such a list is showing SHALL act on the device at that position exactly as selecting that row does — opening it for editing on the Manage Devices list and beginning the connect/pair flow on the Use Remote picker — and SHALL therefore follow the current order rather than the order the devices were added in. A digit that does not correspond to a listed device SHALL do nothing. Numbering is a display and shortcut concern only: it SHALL NOT change the stored device name.

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

#### Scenario: Use Remote picker reflects a reordering
- **WHEN** the user reorders the devices on the Manage Devices list and then opens Use Remote
- **THEN** the picker lists the devices in the reordered order with numbering to match

#### Scenario: Digit follows the reordered positions
- **WHEN** the devices have been reordered and the user presses a digit on either list
- **THEN** the action applies to the device now at that position, not to the device that was there before the reordering
