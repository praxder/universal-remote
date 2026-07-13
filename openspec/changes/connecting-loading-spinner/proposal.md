## Why

When a user picks a device in Use Remote, the app awaits the TV connection inside the selection handler and shows nothing on screen — the UI appears frozen for the seconds a connect takes, and if the TV is unreachable the connect can hang indefinitely or crash the flow. Users need visible feedback that work is happening and a graceful path when a connection fails.

## What Changes

- Connecting to a device SHALL show a modal loading spinner (overlay, device list dimmed behind) instead of freezing the screen — for both the direct-connect path (stored credential) and the after-pairing path.
- The connect step SHALL run off the event handler so the UI stays responsive, and SHALL be cancellable while in progress.
- A failed connect SHALL surface an in-modal error state ("Couldn't connect to …") offering **Retry** and **Back**, rather than an unhandled crash.
- Adapter connects SHALL be bounded by a timeout and SHALL report a distinct connection-failure error when a device is unreachable, so the failure state surfaces promptly instead of the spinner spinning forever. (Today only Samsung *pairing* has a timeout; neither adapter's *connect* does.)

## Capabilities

### New Capabilities
<!-- none — this change modifies existing capabilities -->

### Modified Capabilities
- `tui-remote`: the Use Remote connect step gains a modal loading spinner, a cancellable connect, and a connect-failure error state with Retry/Back.
- `remote-control-core`: the connect contract gains a bounded-time guarantee and a distinct connection-failure error for unreachable devices.

## Impact

- **Code**
  - `src/universal_remote/tui/remote_flow.py`: new `ConnectingModal(ModalScreen)`; `UseRemoteScreen` pushes it for the direct-connect path (removing the inline `await` in the selection handler); `PairingScreen` pairs only, then hands off to the modal. Screen-stack ownership moves to `UseRemoteScreen` via dismiss/callback so no transient screen is orphaned under `RemoteScreen`.
  - `src/universal_remote/errors.py`: new `ConnectionFailedError(UniversalRemoteError)`.
  - `src/universal_remote/adapters/lg.py` and `.../samsung.py`: bound `connect` with a timeout and wrap transport failures as `ConnectionFailedError`.
- **Tests**
  - `tests/fakes.py`: add a connect-failure mode to `FakeAdapter`.
  - `tests/test_tui_remote_flow.py`: the stored-credential and after-pairing flows now route through the modal; add a connect-failure + Retry test.
- **Dependencies**: none new (Textual `ModalScreen`/`LoadingIndicator` are built in).
- **No breaking changes** to the public adapter/session API; `connect` still returns a `Session` on success.
