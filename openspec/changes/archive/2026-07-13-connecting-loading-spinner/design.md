## Context

Use Remote connects to a TV in two places in `tui/remote_flow.py`:

- **Direct connect** (`UseRemoteScreen._open_remote`): `await adapter.connect(device)` is awaited *inside* the `on_option_list_option_selected` handler. Nothing on screen changes and the `OptionList` message pump is blocked, so the UI appears frozen for the seconds a connect takes.
- **After pairing** (`PairingScreen._pair_and_connect`): pairs, stores the credential, then connects — all in one worker, under a screen still labelled "Pairing…".

The pairing path already runs work in a `run_worker` with a cancel affordance; the direct path does not. Neither adapter's `connect` has a timeout (`lg.py` calls `client.connect()` raw; `samsung.py` passes `timeout=` to `pair` but not `connect`), and neither wraps transport failures — an unreachable TV can hang indefinitely and any error propagates raw into a worker crash.

## Goals / Non-Goals

**Goals:**
- Show a modal loading spinner while connecting, for both connect paths, with the UI responsive and the connect cancellable.
- Surface connect failures as an in-modal error state with Retry/Back instead of a freeze or crash.
- Make connect fail promptly (bounded timeout) and raise a distinct `ConnectionFailedError` so the error state actually shows.
- Keep the screen stack clean (`[UseRemote, Remote]`) with no orphaned transient screens.

**Non-Goals:**
- No loading affordance for key/text sends or session close — they ride an already-open socket and are effectively instant (out of scope by decision).
- Pairing stays a full screen (it needs the "accept the popup on your TV" guidance); only the connect step becomes a modal.
- No new external dependency; no change to the public `Adapter`/`Session` API shape.

## Decisions

### Modal via `ModalScreen` + `LoadingIndicator`
Use Textual's `ModalScreen` so the device list stays visible and dimmed behind the dialog, and compose a `LoadingIndicator` widget inside a small dialog box alongside a label and Cancel button.
- *Alternative — full `Screen`:* rejected; the user wants an overlay, not a page swap.
- *Alternative — `widget.loading = True`:* rejected; that overlay hides the widget's children, so the Cancel button and label would not be visible during loading.

### Work runs in a cancellable worker
`ConnectingModal.on_mount` starts `run_worker(self._connect(), exclusive=True)`, mirroring `PairingScreen`. Cancel/Back MUST call `self._worker.cancel()` (not just dismiss) so an in-flight connect is actually abandoned. The direct-connect handler no longer awaits `connect` — it pushes the modal and returns immediately, so the message pump is never blocked.

### One modal, two visual states
The modal renders a **loading** state (spinner + Cancel) and, on failure, swaps its content to an **error** state (message naming the device + Retry + Back) in place. Retry restarts the worker; Back/Cancel dismiss. Keeping the error inside the modal gives the Retry button a home (a toast could not).

### `UseRemoteScreen` owns forward navigation; transient screens dismiss themselves
This is the subtlety most likely to go wrong. To guarantee the stack ends as `[UseRemote, Remote]` with nothing orphaned underneath:
- `ConnectingModal` calls `self.dismiss(session)` on success and `self.dismiss(None)` on cancel/give-up. It never pushes `RemoteScreen` itself.
- `UseRemoteScreen` pushes the modal with a callback; the callback, on a non-`None` session, pushes `RemoteScreen` (built from the session plus the device/adapter it initiated the connect for).
- `PairingScreen` pairs only, stores the credential, and `self.dismiss(device)` on success / `dismiss(None)` on cancel. `UseRemoteScreen`'s pairing callback then starts the connect (pushes the modal). Pairing never pushes the modal or the remote itself.

This replaces the current `switch_screen`/inline-push mix with a single ownership rule.

### Connect timeout + `ConnectionFailedError` in the adapters
Add `ConnectionFailedError(UniversalRemoteError)` to `errors.py`. In each adapter's `connect`:
- **Samsung:** pass `timeout=` to the connect remote (as `pair` already does).
- **LG:** wrap `client.connect()` in `asyncio.wait_for(..., timeout)` (the client factory does not take a connect timeout).
- Both: catch transport failures and `asyncio.TimeoutError` and re-raise as `ConnectionFailedError` (`from exc`). The TUI catches `ConnectionFailedError` inside the worker and transitions to the error state.

## Risks / Trade-offs

- **Uncaught worker exceptions crash the app** → the worker wraps `connect` in try/except and drives the error state; only `ConnectionFailedError` (and `CancelledError`, which is expected on Cancel) are anticipated.
- **Spinner-mid-flight is racy to test** with instant fakes → do not assert "spinner is visible during connect". Pin the durable outcomes instead: success routes through the modal and ends on `RemoteScreen`; a raising adapter yields the error state; Retry after failure re-attempts and succeeds. Requires a connect-failure mode on `FakeAdapter` in `tests/fakes.py`.
- **LG client may not honor cancellation cleanly** on `wait_for` timeout → acceptable; `disconnect`/GC releases the socket, and the user already sees the error state. Not worth special handling now.
- **Behavioral test churn** → `test_given_a_stored_credential_when_selected_then_it_connects_without_pairing` and the after-pairing test now traverse the modal; they are updated, not deleted.
