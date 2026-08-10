## ADDED Requirements

### Requirement: The remote releases its device session when it is torn down

The remote SHALL close its live device session whenever the remote surface is torn down — both when the user leaves it with Go Back and when the user quits the application while it is open. An adapter session that owns a network client (for example the Roku ECP or Fire TV HTTP client) SHALL therefore be released on exit rather than left open to be garbage-collected, which would print a client-session warning to the terminal after the application has exited. Closing SHALL be idempotent, so a session already closed on the way out is not closed twice.

Releasing the session on the way out SHALL be bounded and SHALL NOT surface: a device that stopped answering MUST NOT stall the exit, and a failure to release MUST NOT print anything to the terminal. A release that fails or exceeds the bound SHALL be logged to the error log and abandoned, and the application SHALL exit regardless.

While the remote stays open — including when a modal such as text entry or the macros list is shown over it — the session SHALL remain connected. Quitting from such a modal SHALL still release the remote's session.

#### Scenario: A release that fails does not stop the exit

- **WHEN** the user quits while the remote is open and closing the session raises
- **THEN** the failure is logged, nothing is printed to the terminal, and the application still exits

#### Scenario: A release that hangs is abandoned

- **WHEN** the user quits while the remote is open and closing the session does not complete within the bound
- **THEN** the release is abandoned and the application exits rather than waiting on the device

#### Scenario: Quitting from a modal over the remote closes the session

- **WHEN** the user quits while a modal is open over the remote
- **THEN** the remote's live device session is still closed

#### Scenario: Quitting from the remote closes the session

- **WHEN** the user quits the application while the remote is open
- **THEN** the live device session is closed as part of the shutdown, and nothing is printed to the terminal after the application exits

#### Scenario: Leaving the remote closes the session

- **WHEN** the user leaves the remote with Go Back
- **THEN** the live device session is closed before the remote is popped

#### Scenario: A modal over the remote leaves the session open

- **WHEN** a modal is opened and dismissed over the remote
- **THEN** the remote stays open with its session still connected
