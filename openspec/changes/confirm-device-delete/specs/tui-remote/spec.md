## MODIFIED Requirements

### Requirement: Device management screens
The Manage Devices mode SHALL present a "Devices" ASCII-art banner, the saved devices, and an always-present add entry as the last row of the list, backed by the device store and exposing add, edit, and delete. When one or more devices are saved, the mode SHALL list the devices first, then a separator, then the add entry; when no devices are saved, the list SHALL show only the add entry. Selecting the add entry — by Enter or by mouse click — SHALL open the add flow. Selecting a device row — by Enter or by mouse click — SHALL open that device for editing. Deleting a device SHALL be triggered by the Backspace key while a device row is highlighted, and SHALL require the user to confirm before the device is removed: the system SHALL present a confirmation prompt naming the device, remove the device only when the user confirms, and leave the store unchanged when the user cancels. Pressing Backspace while the add entry is highlighted SHALL do nothing.

#### Scenario: Devices listed above the add row
- **WHEN** the user opens Manage Devices with one or more saved devices
- **THEN** the saved devices are displayed first, followed by a separator, then an add entry as the last row

#### Scenario: First run shows only the add entry
- **WHEN** the user opens Manage Devices with no saved devices
- **THEN** the list shows only the add entry as its single row

#### Scenario: Add entry opens the add flow
- **WHEN** the user selects the add entry by Enter or by mouse click
- **THEN** the application presents the IP-entry and confirmation flow and saves the result

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

#### Scenario: Backspace on the add entry does nothing
- **WHEN** the add entry is highlighted and the user presses Backspace
- **THEN** no confirmation prompt is shown and no device is removed
