## Why

An unexpected exception anywhere in the TUI — a worker raising something outside the anticipated error list, a bug in a message handler — tears the app down and dumps a Rich traceback to the terminal. Every current handler catches exactly one anticipated domain error and lets everything else propagate to Textual's `App._handle_exception`, which always exits. The user loses their session and sees a wall of red instead of a recoverable app.

## What Changes

- Add an app-wide safety net: override `App._handle_exception` so an **unexpected** exception surfaces as an error toast and the app stays open, instead of crashing to the terminal.
- Log the full traceback of every caught error to a **file**, so suppressing the terminal dump does not cost debuggability.
- Keep the two-tier split explicit:
  - **Tier 1** — expected domain errors (`UniversalRemoteError` subclasses) stay handled at the seam with tailored UX (inline retry, status line). Their messages are user-safe and shown as-is.
  - **Tier 2** — the global net catches everything unexpected: generic "something went wrong" toast + logged traceback.
- Make routinely-flaky, high-frequency seams best-effort locally so they never reach the net or toast: the reachability probe (`_probe_device`, fires every 5s) and the discovery scan. A failing probe must not produce a toast storm.
- **Scope the net deliberately:** worker and message-handler errors are caught-and-stayed; a compose/mount error still closes the app, because staying open would leave a half-built widget tree wedged.
- Preserve `self._exception` bookkeeping under pilot/test runs so tests still surface bugs via the existing re-raise-at-shutdown path.

## Capabilities

### New Capabilities
- `app-error-handling`: How the application responds to errors app-wide — the global safety net for unexpected exceptions, error-toast presentation, file logging of tracebacks, the boundary between caught-and-stayed vs. app-closing errors, and the rule that routinely-flaky seams stay best-effort and silent.

### Modified Capabilities
<!-- None. Tier-1 domain-error handling behavior at existing seams is unchanged; this change adds a new cross-cutting capability rather than altering existing spec requirements. -->

## Impact

- **New code:** a file logger for tracebacks; a `_handle_exception` override on `UniversalRemoteApp` (`src/universal_remote/tui/app.py`).
- **Touched seams:** `_probe_device` (`tui/remote_flow.py`) and the discovery scan (`tui/discover_screen.py`) confirmed/made best-effort so they never reach the net.
- **Dependencies:** none new — uses Textual's built-in `notify` and Python's `logging`.
- **Behavioral:** Ctrl-C is unaffected (`KeyboardInterrupt`/`SystemExit`/`CancelledError` are `BaseException` and never reach the hook). Compose/mount errors still exit.
