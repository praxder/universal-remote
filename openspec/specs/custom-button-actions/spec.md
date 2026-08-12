# custom-button-actions Specification

## Purpose
Let a custom remote button be assigned an action from an extensible catalog — currently Run Custom Script — that is configured, run without blocking the UI, and reports its outcome per the user's choice.
## Requirements
### Requirement: Assignable action catalog
A custom button MAY be assigned an action drawn from an action catalog. The catalog SHALL be extensible: adding a new action type SHALL NOT require reworking the remote surface or the Button Config modal. The catalog SHALL contain two action types, Run Custom Script, whose display label is "Run Custom Script", and Run Macro, whose display label is "Run Macro". The Action Type list SHALL present the catalog's action types for selection.

Every action type SHALL be run through one shared contract: the catalog SHALL pass a running action an execution context carrying the running application — through which an action reports a message to the user, or presents its own modal — the connected device's IP address, the live device session, and the saved macros and custom buttons together with the active device's identity and platform. An action type SHALL read only what it needs from that context. The result of running any action type SHALL be one common result value reporting whether it succeeded, a short human-readable summary, and — where the action type produces them — an exit code and captured output. Widening the context to serve a new action type SHALL NOT require changing an existing action type's runner. An action type that reports its own outcome to the user SHALL declare that, and the shared path SHALL NOT surface such an action's result a second time, so an action that has already reported a failure does not also raise a generic one.

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

### Requirement: Run Custom Script configuration
The Run Script configuration modal SHALL offer a source toggle between Script File and Inline Script. When Script File is selected it SHALL present a single-line input for a path to a shell script; when Inline Script is selected it SHALL present a multi-line editor for shell script text. The modal SHALL offer a Results toggle between Don't Show and Show. The modal SHALL display a helpline stating that `REMOTE_IP` is set in the script's environment to the connected device's IP address. The modal SHALL provide OK and Cancel controls. Selecting OK SHALL store the configured action (source kind, script or path, and results-visibility choice) on the button at the scope chosen in the Button Config modal; Cancel SHALL close the modal without storing an action. When the modal is opened for a button that already has a Run Custom Script action, it SHALL prefill its controls from the stored action — the source toggle, the script text or file path, and the Results choice — so re-editing continues from the saved values rather than an empty form.

#### Scenario: Configure an inline script
- **WHEN** the user selects Inline Script, enters script text, chooses a Results option, and selects OK
- **THEN** the inline script and results choice are stored as the button's action for the chosen scope

#### Scenario: Configure a script file
- **WHEN** the user selects Script File, enters a path to a shell script, and selects OK
- **THEN** the script-file path is stored as the button's action for the chosen scope

#### Scenario: Helpline names REMOTE_IP
- **WHEN** the Run Script configuration modal is open
- **THEN** a helpline states that `REMOTE_IP` is provided in the environment as the connected device's IP address

#### Scenario: Cancel stores nothing
- **WHEN** the user opens the Run Script configuration modal and selects Cancel
- **THEN** no action is stored and the button is unchanged

#### Scenario: Re-editing prefills the stored action
- **WHEN** the user reopens the Run Script configuration for a button that already has a Run Custom Script action
- **THEN** the source toggle, the script text or file path, and the Results choice are prefilled from the stored action rather than opening blank

### Requirement: Non-blocking script execution with REMOTE_IP
Running a custom button's Run Custom Script action SHALL execute the configured shell script without blocking the user interface, in a background worker using an asynchronous subprocess. Both source kinds SHALL run through the shell: an inline script SHALL run as shell text, and a script file SHALL be run by passing its path to the shell rather than executing the file directly, so a file needs neither an execute bit nor a shebang line. A file path SHALL have a leading `~` expanded to the user's home directory. The script's environment SHALL include `REMOTE_IP` set to the connected device's IP address; `REMOTE_IP` SHALL be the only value the application injects. Execution SHALL be bounded by a fixed 30-second timeout, not user-configurable, that terminates a script still running when it elapses, and a terminated script SHALL be treated as a failure. A script that cannot be started — a script-file path that is not an existing file, or any other spawn failure — SHALL be reported as a failure rather than crashing the remote.

#### Scenario: Script runs without freezing the UI
- **WHEN** the user activates a custom button whose action is a long-running script
- **THEN** the script runs in the background and the remote remains responsive

#### Scenario: REMOTE_IP is available to the script
- **WHEN** a custom-button script runs while connected to a device at a given IP
- **THEN** the script's environment contains `REMOTE_IP` set to that device's IP address

#### Scenario: Hung script is terminated
- **WHEN** a script is still running when the execution timeout elapses
- **THEN** the script is terminated and the run is treated as a failure

#### Scenario: A script file runs through the shell
- **WHEN** a Run Custom Script action points at a script file that has no shebang line and no execute permission
- **THEN** the file is run through the shell and executes normally rather than failing with an exec-format error

#### Scenario: Unstartable script fails gracefully
- **WHEN** a Run Custom Script action points at a path that cannot be executed
- **THEN** the run is reported as a failure and the remote does not crash

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

### Requirement: User-shell trust boundary
The Run Custom Script action SHALL execute arbitrary shell provided by the user, on the user's own machine, under the user's own privileges. The application SHALL NOT sandbox, vet, or restrict script contents, and the execution timeout SHALL serve as a reliability guard rather than a security control. This trust boundary SHALL be documented so that running user-authored shell is a deliberate, disclosed capability.

#### Scenario: Scripts run unrestricted by design
- **WHEN** a user configures and runs any shell script
- **THEN** the application executes it without sandboxing or content restrictions, consistent with the documented trust boundary

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

