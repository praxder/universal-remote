## MODIFIED Requirements

### Requirement: Custom buttons on the remote
The remote SHALL present exactly five custom buttons in a dedicated row. Each button SHALL show its configured title resolved for the active device, or its default title `Custom N` (where `N` is the button's 1-based position) when no title is configured for that device. Each custom button MUST be clickable with the mouse. Clicking a custom button SHALL run its assigned action when one is resolved for the active device, and SHALL open the button's configuration modal when no action is assigned. A custom button MAY also be activated by an assigned keyboard shortcut (see the keyboard-shortcuts catalog), which SHALL behave identically to clicking that button — running its resolved action, or opening its configuration when none is assigned. To re-edit a button that has an assigned action, the user SHALL use a distinct edit gesture: pressing an edit-mode key SHALL arm edit-mode, and the next activation of a custom button — whether by clicking it or by pressing its keyboard shortcut — SHALL open that button's configuration modal instead of running its action, after which edit-mode SHALL clear. While edit-mode is armed, the custom buttons SHALL show a visual indicator distinguishing the armed edit state from their normal run appearance, and that indicator SHALL clear together with edit-mode.

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
