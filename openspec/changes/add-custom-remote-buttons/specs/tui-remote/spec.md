## MODIFIED Requirements

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

### Requirement: Text-entry focus behavior
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

## ADDED Requirements

### Requirement: Custom buttons on the remote
The remote SHALL present exactly five custom buttons in a dedicated row. Each button SHALL show its configured title resolved for the active device, or its default title `Custom N` (where `N` is the button's 1-based position) when no title is configured for that device. Each custom button MUST be clickable with the mouse. Each custom button MAY also be activated by an assigned keyboard shortcut (see the keyboard-shortcuts catalog), which SHALL behave identically to clicking that button. In this phase a custom button carries a title but no runnable action; activating a custom button (by click or shortcut) SHALL open its configuration modal.

#### Scenario: Custom buttons show defaults when unconfigured
- **WHEN** the user opens Use Remote for a device with no custom-button titles saved
- **THEN** the five custom buttons read `Custom 1`, `Custom 2`, `Custom 3`, `Custom 4`, and `Custom 5`

#### Scenario: Custom button shows its resolved title
- **WHEN** a custom button has a title configured that applies to the active device
- **THEN** that button shows the configured title instead of its `Custom N` default

#### Scenario: Clicking a custom button opens its configuration
- **WHEN** the user clicks a custom button
- **THEN** the Button Config modal for that button opens

#### Scenario: A keyboard shortcut activates a custom button
- **WHEN** the user has assigned a shortcut to a custom button and presses it on the remote
- **THEN** the same thing happens as clicking that button — in this phase, its configuration modal opens

### Requirement: Custom button configuration modal
Clicking a custom button SHALL open a Button Config modal whose heading is the static text "Configure Custom Button". The modal SHALL contain a button-title text input, a three-way scope selector offering This Device, Device Type, and Global, a disabled Action Type control presented as a placeholder for a later version, and OK and Cancel controls. Selecting OK SHALL save the entered title for the button at the selected scope, persist it, and update the button on the remote to show the newly resolved title and resize to fit it immediately, without requiring the remote to be reopened. Selecting Cancel SHALL close the modal without changing any saved title. When opened, the scope selector SHALL preselect the scope the button's shown title resolves from — the specific device, then device type, then global — so reopening the modal reflects where the title is actually stored; when no title is configured at any scope it SHALL default to This Device.

#### Scenario: Save a title for this device
- **WHEN** the user opens a custom button's config modal, enters a title, leaves the scope on This Device, and selects OK
- **THEN** the modal closes and that button on the remote shows the entered title for the current device

#### Scenario: Saved title resizes the button immediately
- **WHEN** the user saves a title that is longer or shorter than the current one
- **THEN** the button on the remote shows the new title and its width adjusts to fit immediately, without reopening the remote

#### Scenario: Scope selector reflects where the title is stored
- **WHEN** a button's title was saved at the Global scope and the user reopens its config modal
- **THEN** the scope selector shows Global selected rather than This Device

#### Scenario: Heading is static text
- **WHEN** the user opens any custom button's config modal
- **THEN** the heading reads "Configure Custom Button" regardless of which button was opened

#### Scenario: Save a title for the device type
- **WHEN** the user enters a title, sets the scope to Device Type, and selects OK
- **THEN** the title is saved for the current device's type and the button shows it

#### Scenario: Save a title globally
- **WHEN** the user enters a title, sets the scope to Global, and selects OK
- **THEN** the title is saved for the button regardless of device or device type and the button shows it

#### Scenario: Cancel discards changes
- **WHEN** the user opens a custom button's config modal, edits the title, and selects Cancel
- **THEN** the modal closes and the button's saved title is unchanged

#### Scenario: Action Type is a disabled placeholder
- **WHEN** the Button Config modal is open
- **THEN** the Action Type control is shown disabled and cannot be activated
