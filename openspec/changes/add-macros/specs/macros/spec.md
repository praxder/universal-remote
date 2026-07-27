## ADDED Requirements

### Requirement: Macros list modal
Activating the remote's Macros control SHALL open a modal listing every saved macro by
name, in saved order. The list SHALL be navigable with the Up and Down arrow keys and
with the Vim keys `k` and `j`, matching the navigation used elsewhere in the
application. When no macros are saved, the list SHALL show a single placeholder row
reading that there are no macros yet; that row SHALL NOT be selectable and SHALL NOT
open a macro. The modal SHALL provide a Close control that dismisses it without change,
and a Create Macro control that begins recording a new macro. Pressing Enter on a
selected macro row SHALL open that macro's detail modal.

#### Scenario: List shows saved macros
- **WHEN** the user activates the Macros control with one or more macros saved
- **THEN** the modal lists each saved macro by name

#### Scenario: Empty list shows a placeholder
- **WHEN** the user activates the Macros control with no macros saved
- **THEN** the list shows a single row stating there are no macros yet

#### Scenario: Placeholder row is not selectable
- **WHEN** the list shows the no-macros placeholder and the user presses Enter on it
- **THEN** no detail modal opens and nothing is recorded or played

#### Scenario: List navigable by arrows and by Vim keys
- **WHEN** the user presses Up, Down, `k`, or `j` while the macros list is focused
- **THEN** the highlighted row moves accordingly

#### Scenario: Close dismisses the list
- **WHEN** the user activates Close on the macros list
- **THEN** the modal is dismissed and no macro is created, changed, or deleted

#### Scenario: Enter opens a macro's detail
- **WHEN** the user highlights a saved macro and presses Enter
- **THEN** that macro's detail modal opens

### Requirement: Recording a new macro
Activating Create Macro SHALL dismiss the macros list modal, return the user to the live
remote, and place the remote in a recording state that captures every subsequent remote
interaction as an ordered step until the user stops or cancels. Recording SHALL continue
across any number of interactions. Activating the remote's Stop control SHALL end
recording, save the captured steps as a new macro under a default name, and reopen the
macros list modal with the new macro present and selected. Pressing the Go Back key
while recording SHALL cancel recording, discard everything captured, and reopen the
macros list modal unchanged. A recording ended with no captured steps SHALL NOT create a
macro; the application SHALL report that nothing was recorded and reopen the macros list
unchanged.

#### Scenario: Create Macro returns to the live remote
- **WHEN** the user activates Create Macro on the macros list
- **THEN** the modal is dismissed and the live remote is shown in its recording state

#### Scenario: Interactions are captured in order
- **WHEN** the user presses several remote keys while recording
- **THEN** each press is captured as a step, in the order performed

#### Scenario: Stop saves the macro and reopens the list
- **WHEN** the user activates the Stop control after capturing at least one step
- **THEN** recording ends, a new macro holding the captured steps is saved, and the macros list reopens showing that macro

#### Scenario: Go Back cancels the recording
- **WHEN** the user presses the Go Back key while recording
- **THEN** nothing is saved and the macros list reopens unchanged

#### Scenario: An empty recording creates nothing
- **WHEN** the user activates the Stop control without having performed any interaction
- **THEN** no macro is created, the application reports that nothing was recorded, and the macros list reopens unchanged

### Requirement: Captured step types
While recording, the application SHALL capture a step for each of the following, and
nothing else: a device key sent by clicking a remote button or by pressing its keyboard
shortcut; a text send completed through the text-entry modal; and a custom button whose
resolved action is dispatched. A key SHALL be captured only when it was actually sent — a
key the active adapter does not support, or a send that failed, SHALL NOT become a step. A
custom button's action SHALL be captured when it is dispatched rather than when it
finishes, since a custom action runs in the background and its outcome is not known at the
moment of activation. A custom button that opens its configuration modal instead of
running — because it has no assigned action, or because edit-mode was armed — SHALL NOT
become a step. A captured custom-button
action SHALL be stored as a frozen copy of that action, not as a reference to the button,
so the step continues to do what it did when recorded even if the button is later
reconfigured or the macro is replayed on a device where that button resolves differently.

#### Scenario: A clicked key is captured
- **WHEN** the user clicks an enabled remote key button while recording
- **THEN** a step for that key is captured

#### Scenario: A key sent by shortcut is captured
- **WHEN** the user presses a remote key's keyboard shortcut while recording
- **THEN** a step for that key is captured, identically to clicking the button

#### Scenario: An unsupported key is not captured
- **WHEN** the user presses the shortcut for a key the active adapter does not support while recording
- **THEN** no step is captured

#### Scenario: A failed send is not captured
- **WHEN** a key send fails because the device is unreachable while recording
- **THEN** no step is captured for that key

#### Scenario: Text entry is captured
- **WHEN** the user sends text through the text-entry modal while recording
- **THEN** a step holding that text is captured

#### Scenario: A dispatched custom button is captured as a frozen copy
- **WHEN** the user activates a custom button whose assigned action is dispatched while recording
- **THEN** a step holding a copy of that action is captured, without waiting for the action to finish

#### Scenario: Reconfiguring a button does not change a captured step
- **WHEN** a macro holds a step captured from a custom button and that button is later reconfigured with a different action
- **THEN** the macro's step still performs the action as it was when captured

#### Scenario: Opening a button's configuration is not captured
- **WHEN** the user activates a custom button that has no assigned action, or activates one with edit-mode armed, while recording
- **THEN** its configuration modal opens and no step is captured

### Requirement: Nested macros are refused
A macro SHALL NOT contain a step that invokes another macro. When the user activates a
custom button whose resolved action is Run Macro while recording, the application SHALL
run that action but SHALL NOT capture it as a step, and SHALL report that nested macros
are not supported. Should a nested Run Macro step nevertheless be present — for example
in a hand-edited preferences file — playback SHALL refuse that step, report it, and
continue with the remaining steps rather than recursing.

#### Scenario: Recording refuses to capture a Run Macro button
- **WHEN** the user activates a custom button whose action is Run Macro while recording
- **THEN** no step is captured and the application reports that nested macros are not supported

#### Scenario: Playback refuses a nested macro step
- **WHEN** a macro being played reaches a step that invokes another macro
- **THEN** that step is not run, the refusal is reported, and playback continues with the next step

### Requirement: Default macro names use a monotonic counter
A newly recorded macro SHALL be named `Macro N`, where `N` comes from a counter that is
persisted with the macro registry and increases with each macro created. The counter
SHALL NOT be derived from the number of saved macros, so deleting a macro never causes a
later macro to reuse a name.

#### Scenario: Successive macros are numbered in sequence
- **WHEN** the user records three macros in a row without renaming them
- **THEN** they are named `Macro 1`, `Macro 2`, and `Macro 3`

#### Scenario: A deleted name is not reused
- **WHEN** the user has recorded `Macro 1` and `Macro 2`, deletes `Macro 2`, and records another macro
- **THEN** the new macro is named `Macro 3`

### Requirement: Macro detail modal edits a draft
The macro detail modal SHALL present an editable text input holding the macro's name and
a navigable list of its steps, each step described in a human-readable form naming what
it does. All edits made in the detail modal — the name, the order of steps, deletions,
insertions, and pause values — SHALL be held in an in-memory draft and SHALL NOT be
persisted until the user saves. The modal SHALL provide Save, Close, and Delete controls:
Save SHALL persist the draft's name and steps to the macro and close the modal; Close
SHALL discard every unsaved edit and close the modal; Delete SHALL remove the macro
entirely and close the modal. After Save, Close, or Delete, the macros list SHALL be
shown reflecting the outcome.

#### Scenario: Detail modal shows the name and steps
- **WHEN** the user opens a macro's detail modal
- **THEN** the macro's name is shown in an editable input and each of its steps is listed with a readable description

#### Scenario: Save persists the edits
- **WHEN** the user renames a macro, reorders its steps, and activates Save
- **THEN** the macro is stored with the new name and step order, and the macros list shows the new name

#### Scenario: Close discards the edits
- **WHEN** the user renames a macro and reorders its steps, then activates Close
- **THEN** the macro is unchanged and the macros list shows its original name

#### Scenario: Delete removes the macro
- **WHEN** the user activates Delete on a macro's detail modal
- **THEN** the macro is removed and the macros list no longer shows it

### Requirement: Step editing controls
With a step selected in the detail modal, the application SHALL offer controls to move
that step one position earlier in the list, to move it one position later, to delete it,
to record one additional step after it, and to insert a pause after it. Moving the first
step earlier or the last step later SHALL do nothing. Every one of these SHALL alter only
the draft, taking effect on the persisted macro when the user saves.

#### Scenario: Move a step earlier
- **WHEN** the user selects a step that is not the first and activates the move-up control
- **THEN** the step swaps position with the step above it in the listed order

#### Scenario: Move a step later
- **WHEN** the user selects a step that is not the last and activates the move-down control
- **THEN** the step swaps position with the step below it in the listed order

#### Scenario: Moving beyond the ends does nothing
- **WHEN** the user activates move-up on the first step, or move-down on the last step
- **THEN** the step order is unchanged

#### Scenario: Delete a step
- **WHEN** the user selects a step and activates the delete-step control
- **THEN** that step is removed from the listed steps

#### Scenario: Step edits are not persisted until save
- **WHEN** the user deletes a step and then activates Close instead of Save
- **THEN** the macro still holds that step

### Requirement: Adding one step by recording
Activating the add-step control in the detail modal SHALL dismiss the modal, return the
user to the live remote in a recording state that captures exactly one interaction, and
then reopen the detail modal with that single step inserted after the step that was
selected. The reopened detail modal SHALL carry every unsaved edit the draft already held,
so a rename or reorder made before adding a step is not lost. Pressing the Go Back key,
or activating the remote's Cancel control, while capturing one step SHALL return to the
detail modal with the draft unchanged.

#### Scenario: One captured action returns to the detail modal
- **WHEN** the user activates the add-step control and then performs one remote interaction
- **THEN** the remote returns to the detail modal with that interaction inserted as a step after the previously selected step

#### Scenario: Unsaved edits survive adding a step
- **WHEN** the user renames a macro, reorders its steps, activates the add-step control, and performs one interaction
- **THEN** the reopened detail modal still shows the new name and the reordered steps, plus the newly inserted step

#### Scenario: Cancelling the capture leaves the draft unchanged
- **WHEN** the user activates the add-step control and then presses the Go Back key or activates the remote's Cancel control
- **THEN** the detail modal reopens with no step added and the draft otherwise unchanged

### Requirement: Pause steps
Activating the add-pause control in the detail modal SHALL prompt the user for a duration
in milliseconds and insert a pause step holding that duration after the selected step. A
pause step SHALL be listed showing its duration. Selecting an existing pause step and
opening it SHALL reopen the duration prompt prefilled with its current value, so the
duration can be changed. During playback, a pause step SHALL delay for its duration
before the next step runs. A prompt cancelled or given a value that is not a
non-negative whole number of milliseconds SHALL insert or change nothing.

#### Scenario: Insert a pause
- **WHEN** the user selects a step, activates the add-pause control, and enters a duration in milliseconds
- **THEN** a pause step of that duration is inserted after the selected step and is listed with its duration

#### Scenario: Edit a pause duration
- **WHEN** the user opens an existing pause step
- **THEN** the duration prompt opens prefilled with its current value, and entering a new value changes that step

#### Scenario: Playback waits for a pause
- **WHEN** playback reaches a pause step
- **THEN** it waits for that step's duration before running the next step

#### Scenario: An invalid duration inserts nothing
- **WHEN** the user cancels the duration prompt, or enters a value that is not a non-negative whole number
- **THEN** no pause step is inserted and no existing pause is changed

### Requirement: Playback freezes the remote behind a modal
Playing a macro SHALL present a modal reporting that the macro is playing, naming it, and
showing progress through its steps, together with a Cancel control. While that modal is
shown the remote SHALL NOT respond to any keyboard shortcut or button press, so no user
interaction can interleave with the macro's own sends. The modal SHALL dismiss itself when
the last step completes. Activating Cancel, or pressing the Go Back key, SHALL stop
playback at whichever step it has reached and dismiss the modal; steps already performed
SHALL NOT be undone.

#### Scenario: Playback shows a progress modal
- **WHEN** a macro begins playing
- **THEN** a modal names the macro, reports that it is playing, and shows its progress through the steps

#### Scenario: The remote is frozen during playback
- **WHEN** the user presses a remote keyboard shortcut while a macro is playing
- **THEN** the remote does not act on it and no key is sent other than the macro's own steps

#### Scenario: The modal dismisses when playback finishes
- **WHEN** a macro's last step completes
- **THEN** the playback modal dismisses and the remote is usable again

#### Scenario: Cancel stops playback where it is
- **WHEN** the user activates Cancel or presses the Go Back key while a macro is playing
- **THEN** playback stops at the current step, the modal dismisses, and no further steps run

### Requirement: A failed step does not stop playback
When a step fails during playback — an unsupported key, a failed send, a script that exits
non-zero or times out, or a refused nested macro — the application SHALL report that
failure and SHALL continue with the next step. When playback completes, the outcome SHALL
summarise how many steps ran and how many failed. Playback SHALL NOT present a per-step
result modal, even for a captured script step configured to show its results, so nothing
interrupts the run waiting on the user.

#### Scenario: Playback continues past an unsupported key
- **WHEN** a macro played on a device whose adapter lacks support for one of its keys reaches that step
- **THEN** the failure is reported and playback continues with the next step

#### Scenario: Playback continues past a failed script step
- **WHEN** a captured script step exits non-zero during playback
- **THEN** the failure is reported and playback continues with the next step

#### Scenario: A show-results script step does not interrupt playback
- **WHEN** playback runs a captured script step whose stored Results choice is Show
- **THEN** no result modal is presented and playback continues to the next step

#### Scenario: The outcome summarises the run
- **WHEN** a macro finishes playing after some steps failed
- **THEN** the reported outcome states how many steps ran and how many failed

### Requirement: Macros persist with their own identity
Each macro SHALL be stored with a stable identifier that is independent of its name and
its position in the list, so a macro can be renamed or reordered without breaking anything
that refers to it. Invokers SHALL refer to a macro by that identifier rather than holding a
copy of it, so editing a macro takes effect for every invoker at once. An invoker whose
macro no longer exists SHALL report that the macro is missing and SHALL do nothing else.

#### Scenario: Renaming a macro does not break an invoker
- **WHEN** a custom button is assigned a macro and that macro is later renamed
- **THEN** the button still plays that macro

#### Scenario: Editing a macro takes effect for its invokers
- **WHEN** a macro assigned to a custom button has a step added and saved
- **THEN** activating that button plays the macro including the new step

#### Scenario: A missing macro is reported
- **WHEN** the user activates a custom button assigned to a macro that has since been deleted
- **THEN** the application reports that the macro no longer exists and nothing is sent to the device
