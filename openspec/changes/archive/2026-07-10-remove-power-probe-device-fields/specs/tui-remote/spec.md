## MODIFIED Requirements

### Requirement: Device management screens
The Manage Devices mode SHALL present a "Devices" ASCII-art banner, the saved devices, and an always-present add entry as the last row of the list, backed by the device store and exposing add, edit, and delete. When one or more devices are saved, the mode SHALL list the devices first, then a separator, then the add entry; when no devices are saved, the list SHALL show only the add entry. Selecting the add entry — by Enter or by mouse click — SHALL open the add flow. Selecting a device row — by Enter or by mouse click — SHALL open that device for editing. The add and edit screen SHALL present an ASCII-art banner titled "Add Device" when adding and "Edit Device" when editing, styled with the same top and bottom margin as the "Devices" banner.

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

#### Scenario: Add and edit screens show an ASCII-art banner
- **WHEN** the user opens the add flow or the edit flow
- **THEN** the screen shows an ASCII-art banner reading "Add Device" or "Edit Device" respectively, with the same top and bottom margin as the "Devices" banner

### Requirement: On-screen remote surface
The Use Remote mode SHALL present a remote resembling a physical remote with a D-pad (up, down, left, right), OK, Back, Home, volume up, volume down, mute, and a text field. Every button MUST be clickable with the mouse.

#### Scenario: Remote renders the button set
- **WHEN** the user opens Use Remote for a device
- **THEN** the D-pad, OK, Back, Home, volume, mute, and text field are shown

#### Scenario: Button click sends action
- **WHEN** the user clicks a remote button
- **THEN** the corresponding key is sent to the selected device
