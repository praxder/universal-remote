## MODIFIED Requirements

### Requirement: Assignable action catalog
A custom button MAY be assigned an action drawn from an action catalog. The catalog SHALL be extensible: adding a new action type SHALL NOT require reworking the remote surface or the Button Config modal. The catalog SHALL contain two action types, Run Custom Script, whose display label is "Run Custom Script", and Run Macro, whose display label is "Run Macro". The Action Type list SHALL present the catalog's action types for selection.

Every action type SHALL be run through one shared contract: the catalog SHALL pass a running action an execution context carrying the connected device's IP address, the live device session, a means of reporting a message to the user, and the saved macros and custom buttons together with the active device's identity and platform. An action type SHALL read only what it needs from that context. The result of running any action type SHALL be one common result value reporting whether it succeeded, a short human-readable summary, and — where the action type produces them — an exit code and captured output. Widening the context to serve a new action type SHALL NOT require changing an existing action type's runner. An action type that reports its own outcome to the user SHALL declare that, and the shared path SHALL NOT surface such an action's result a second time, so an action that has already reported a failure does not also raise a generic one.

#### Scenario: Action Type list shows the catalog
- **WHEN** the user opens the Action Type list from the Button Config modal
- **THEN** it lists the available action types, which are "Run Custom Script" and "Run Macro"

#### Scenario: Selecting an action type opens its configuration
- **WHEN** the user selects Run Custom Script from the Action Type list
- **THEN** the Run Script configuration modal opens

#### Scenario: Selecting Run Macro opens its configuration
- **WHEN** the user selects Run Macro from the Action Type list
- **THEN** the macro picker opens

#### Scenario: An action that reports its own outcome is not reported twice
- **WHEN** an action type that reports its own outcome returns an unsuccessful result from a custom button
- **THEN** the shared path raises no additional failure notification of its own

#### Scenario: An action reaches the live session through the context
- **WHEN** an action type that sends keys to the device is run from a custom button
- **THEN** it reaches the connected device's live session through the execution context rather than being given only the device's IP address

### Requirement: Script results visibility
The Results choice stored with a Run Custom Script action SHALL control how a run surfaces its outcome when that action is run directly — that is, when the user activates the custom button holding it. When Don't Show is selected, a successful run (zero exit code) SHALL produce no visible output, and a failed run (non-zero exit, timeout, or start failure) SHALL raise an error notification describing the failure. When Show is selected, both success and failure SHALL be presented in a result modal reporting the outcome together with the script's exit code and its full output (stdout and stderr); the modal SHALL be scrollable so that long output is presented in full rather than truncated.

The Results choice SHALL NOT apply when the action is run as a step inside a macro. Macro playback presents its own progress modal and reports a failing step as an error notification while aborting the run, so a captured script step SHALL NOT present a result modal regardless of its stored Results choice — nothing may interrupt a run waiting on the user. The macros capability owns that behavior.

#### Scenario: Quiet success when results hidden
- **WHEN** a script configured with Don't Show exits successfully
- **THEN** no result is shown to the user

#### Scenario: Error surfaced when results hidden
- **WHEN** a script configured with Don't Show exits with a non-zero code
- **THEN** an error notification describes the failure

#### Scenario: Result shown when results visible
- **WHEN** a script configured with Show finishes, whether it succeeds or fails
- **THEN** a scrollable result modal reports the outcome with the script's exit code and its full, untruncated output

#### Scenario: Results choice does not apply during macro playback
- **WHEN** a macro being played reaches a captured script step that succeeds and whose stored Results choice is Show
- **THEN** no result modal is presented and playback continues to the next step

#### Scenario: A failing script step during playback shows no result modal
- **WHEN** a macro being played reaches a captured script step that fails and whose stored Results choice is Show
- **THEN** no result modal is presented, the failure is reported as an error notification, and the run aborts

## ADDED Requirements

### Requirement: Run Macro configuration
The Run Macro configuration SHALL present the saved macros for selection by name and SHALL provide OK and Cancel controls. Selecting a macro and confirming SHALL store an action that refers to that macro by its stable identifier — never a copy of the macro — on the button at the scope chosen in the Button Config modal, so editing the macro afterwards changes what the button does. Cancel SHALL close without storing an action. When opened for a button that already has a Run Macro action, the configuration SHALL preselect the macro that action refers to. When no macros are saved, the configuration SHALL state that there are none to choose and SHALL store no action. Run Macro SHALL NOT offer a results-visibility choice: playback presents its own progress modal and reports a failing step as an error notification while aborting the run.

#### Scenario: Assign a macro to a button
- **WHEN** the user selects Run Macro, chooses a saved macro, and confirms
- **THEN** an action referring to that macro is stored on the button at the chosen scope

#### Scenario: The stored action refers to the macro rather than copying it
- **WHEN** a button has been assigned a macro and that macro is later edited and saved
- **THEN** activating the button plays the edited macro

#### Scenario: Re-editing preselects the assigned macro
- **WHEN** the user reopens the Run Macro configuration for a button that already has a Run Macro action
- **THEN** the macro that action refers to is preselected

#### Scenario: Cancel stores nothing
- **WHEN** the user opens the Run Macro configuration and selects Cancel
- **THEN** no action is stored and the button is unchanged

#### Scenario: No macros to choose from
- **WHEN** the user opens the Run Macro configuration with no macros saved
- **THEN** it states that there are no macros to choose and stores no action

#### Scenario: Run Macro offers no results toggle
- **WHEN** the user opens the Run Macro configuration
- **THEN** no results-visibility choice is presented
