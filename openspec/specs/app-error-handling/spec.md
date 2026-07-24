# app-error-handling Specification

## Purpose
Keep the running app open when unexpected errors occur by catching them at a global net that toasts and logs, while leaving expected domain errors to their local seams and letting interrupts pass through.
## Requirements
### Requirement: Unexpected errors keep the app open with an error toast

When an unexpected exception reaches the application's exception handler while the app is running, the application SHALL remain open and SHALL present an error toast, instead of tearing down and printing a traceback to the terminal. An unexpected exception is any exception the code did not anticipate and handle at its seam. The toast SHALL use error severity and SHALL carry a concise, human-readable message; it MUST NOT contain a raw traceback.

#### Scenario: A worker raises an unexpected exception
- **WHEN** a background worker raises an exception that is not handled at its seam while the app is running
- **THEN** the app stays open on its current screen
- **AND** an error-severity toast is shown describing that something went wrong

#### Scenario: A screen message handler raises an unexpected exception
- **WHEN** a screen's event or message handler raises an exception that is not handled locally while the app is running
- **THEN** the app stays open
- **AND** an error-severity toast is shown

#### Scenario: No terminal traceback on a caught error
- **WHEN** the application catches an unexpected exception and stays open
- **THEN** no Rich traceback is printed to the terminal for that error

#### Scenario: The net never crashes on its own reporting
- **WHEN** logging or toasting the caught error itself fails (for example an unwritable log directory)
- **THEN** that secondary failure is suppressed and the app still stays open

### Requirement: Every caught error is logged to a file with its full traceback

Because the terminal traceback is suppressed for caught errors, the application SHALL write the full traceback of every error it catches to a log file, so failures remain investigable. The log entry SHALL include the exception type, message, and complete traceback.

#### Scenario: Traceback written when an error is caught
- **WHEN** the application catches an unexpected exception and shows a toast
- **THEN** the full traceback for that exception is appended to the log file

#### Scenario: Log survives across the caught error
- **WHEN** an error is caught and the app stays open
- **THEN** the app continues running and the logged entry remains on disk for later inspection

### Requirement: Expected domain errors are handled at the seam

Expected domain errors — instances of `UniversalRemoteError` and its subclasses — SHALL continue to be handled at the seam where they occur, with tailored UX (for example an inline retry state or a status-line message), and SHALL NOT depend on the global net. When such an error is surfaced to the user, its own message is user-safe and MAY be shown verbatim.

#### Scenario: Domain error handled locally does not reach the net
- **WHEN** a seam raises a `UniversalRemoteError` that it handles locally
- **THEN** the local handler presents its tailored UX
- **AND** the global error net is not invoked for that error

### Requirement: Routinely-flaky seams stay best-effort and silent

High-frequency or routinely-flaky seams — the reachability probe (which fires on a recurring interval) and the device-discovery scan — SHALL treat failures and timeouts as best-effort: a failure contributes nothing, never aborts sibling work, and never produces a toast. These seams MUST NOT reach the global net.

#### Scenario: A failing reachability probe shows no toast
- **WHEN** a reachability probe fails or times out
- **THEN** no toast is shown
- **AND** the affected device's row reflects the unreachable/unknown state without interrupting the user

#### Scenario: A failing discovery scan shows no toast
- **WHEN** a discovery scan for one adapter fails or times out
- **THEN** that adapter contributes no devices
- **AND** the other adapters' scans are unaffected and no toast is shown

### Requirement: App-closing errors still close the app

An error that leaves the application in a structurally broken state SHALL still close the app rather than leave a half-built, wedged interface. The catch-and-stay behavior applies only once the app has finished its initial mount. Two cases remain out of scope for staying open: an exception during initial startup, compose, or mount (there is no surface to toast on); and an exception on the application's own message pump — a global (app-level) binding action or app-level handler — which Textual tears down after the handler runs. Errors that run in a worker or in a screen's own handler are caught and stayed; these residual cases are not.

#### Scenario: Startup/compose error still exits
- **WHEN** an exception is raised during startup, compose, or mount before the app has finished mounting
- **THEN** the app exits rather than staying open on a half-built screen

#### Scenario: App-level handler error is not held open
- **WHEN** an exception is raised on the application's own message pump (for example a global binding action)
- **THEN** the error is logged, but the app is not guaranteed to stay open

### Requirement: Interrupt and cancellation signals are unaffected

The global net SHALL only affect ordinary exceptions. Interrupt, exit, and cancellation signals — `KeyboardInterrupt`, `SystemExit`, and `asyncio.CancelledError` — SHALL pass through unchanged so that Ctrl-C and normal shutdown continue to work.

#### Scenario: Ctrl-C still quits
- **WHEN** the user presses Ctrl-C
- **THEN** the app shuts down as before and is not held open by the error net
