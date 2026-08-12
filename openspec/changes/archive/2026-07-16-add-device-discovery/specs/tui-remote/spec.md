## MODIFIED Requirements

### Requirement: Device management screens
The Manage Devices mode SHALL present a "Devices" ASCII-art banner, the saved devices, and an always-present add entry as the last row of the list, backed by the device store and exposing add, edit, and delete. When one or more devices are saved, the mode SHALL list the devices first, then a separator, then the add entry; when no devices are saved, the list SHALL show only the add entry. Selecting the add entry — by Enter or by mouse click — SHALL open device discovery (see the "Add device via discovery" requirement). Selecting a device row — by Enter or by mouse click — SHALL open that device for editing. Deleting a device SHALL be triggered by the Backspace key while a device row is highlighted, and SHALL require the user to confirm before the device is removed: the system SHALL present a confirmation prompt naming the device, remove the device only when the user confirms, and leave the store unchanged when the user cancels. The confirmation prompt SHALL default keyboard focus to its cancel action and SHALL let the user move focus between its confirm and cancel actions with the arrow keys. Pressing Backspace while the add entry is highlighted SHALL do nothing. The add and edit screen SHALL present an ASCII-art banner titled "Add Device" when adding and "Edit Device" when editing, styled with the same top and bottom margin as the "Devices" banner. The add and edit screen SHALL order its cells as device type, then name, then IP address. When adding, the device type SHALL be a selector offering the registered platforms by their human-readable names and defaulting to the first; when editing, the device type SHALL be shown as a read-only cell while the name and IP address remain editable. The device-type cell, the name and IP address cells, and the Save button SHALL be reachable both by Tab and by the Up and Down arrow keys — Up moves focus to the previous cell and Down to the next — while the Left and Right arrows continue to move the text cursor within a focused input. Because the Up and Down arrows navigate between cells, the device-type dropdown SHALL open on Enter or Space rather than on an arrow key. The Save button's left edge SHALL be aligned with the cells above it.

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

## ADDED Requirements

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
