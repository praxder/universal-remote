## ADDED Requirements

### Requirement: Assignable action catalog
A custom button MAY be assigned an action drawn from an action catalog. The catalog SHALL be extensible: adding a new action type SHALL NOT require reworking the remote surface or the Button Config modal. In this phase the catalog SHALL contain exactly one action type, Run Custom Script, whose display label is "Run Custom Script". The Action Type list SHALL present the catalog's action types for selection.

#### Scenario: Action Type list shows the catalog
- **WHEN** the user opens the Action Type list from the Button Config modal
- **THEN** it lists the available action types, which in this phase is the single entry "Run Custom Script"

#### Scenario: Selecting an action type opens its configuration
- **WHEN** the user selects Run Custom Script from the Action Type list
- **THEN** the Run Script configuration modal opens

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
The Results choice stored with a Run Custom Script action SHALL control how a run surfaces its outcome. When Don't Show is selected, a successful run (zero exit code) SHALL produce no visible output, and a failed run (non-zero exit, timeout, or start failure) SHALL raise an error notification describing the failure. When Show is selected, both success and failure SHALL be presented in a result modal reporting the outcome together with the script's exit code and its full output (stdout and stderr); the modal SHALL be scrollable so that long output is presented in full rather than truncated.

#### Scenario: Quiet success when results hidden
- **WHEN** a script configured with Don't Show exits successfully
- **THEN** no result is shown to the user

#### Scenario: Error surfaced when results hidden
- **WHEN** a script configured with Don't Show exits with a non-zero code
- **THEN** an error notification describes the failure

#### Scenario: Result shown when results visible
- **WHEN** a script configured with Show finishes, whether it succeeds or fails
- **THEN** a scrollable result modal reports the outcome with the script's exit code and its full, untruncated output

### Requirement: User-shell trust boundary
The Run Custom Script action SHALL execute arbitrary shell provided by the user, on the user's own machine, under the user's own privileges. The application SHALL NOT sandbox, vet, or restrict script contents, and the execution timeout SHALL serve as a reliability guard rather than a security control. This trust boundary SHALL be documented so that running user-authored shell is a deliberate, disclosed capability.

#### Scenario: Scripts run unrestricted by design
- **WHEN** a user configures and runs any shell script
- **THEN** the application executes it without sandboxing or content restrictions, consistent with the documented trust boundary
