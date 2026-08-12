## MODIFIED Requirements

### Requirement: Interrupt and cancellation signals are unaffected

The global net SHALL only affect ordinary exceptions. Interrupt, exit, and cancellation signals — `KeyboardInterrupt`, `SystemExit`, and `asyncio.CancelledError` — SHALL pass through unchanged so that normal shutdown continues to work. Quitting SHALL NOT depend on this passthrough: while the terminal user interface is running, Ctrl-C is delivered as a key event and quits through its binding (see the keyboard-shortcuts capability), not by raising `KeyboardInterrupt`.

#### Scenario: Ctrl-C still quits

- **WHEN** the user presses Ctrl-C
- **THEN** the application shuts down and is not held open by the error net

#### Scenario: Shutdown signals are not swallowed

- **WHEN** a `KeyboardInterrupt`, `SystemExit`, or `asyncio.CancelledError` is raised
- **THEN** it propagates unchanged rather than being logged and suppressed as an ordinary error
