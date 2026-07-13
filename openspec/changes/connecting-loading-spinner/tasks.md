## 1. Error type and adapter connect hardening

- [ ] 1.1 Add `ConnectionFailedError(UniversalRemoteError)` to `src/universal_remote/errors.py`
- [ ] 1.2 Extend `FakeWebOsClient` / `FakeSamsungRemote` in `tests/fakes.py` with a way to simulate a connect that raises a transport error and one that hangs past the timeout
- [ ] 1.3 Write failing tests in `tests/test_lg_adapter.py`: `connect` wraps a transport failure as `ConnectionFailedError`, and a hanging connect fails within the timeout as `ConnectionFailedError`
- [ ] 1.4 Write failing tests in `tests/test_samsung_adapter.py`: same two cases for Samsung `connect`
- [ ] 1.5 Implement LG `connect` (`adapters/lg.py`): wrap `client.connect()` in `asyncio.wait_for(..., timeout)`; catch transport errors and `asyncio.TimeoutError` and re-raise as `ConnectionFailedError` (`from exc`)
- [ ] 1.6 Implement Samsung `connect` (`adapters/samsung.py`): pass `timeout=` to the connect remote (as `pair` does); catch transport errors and timeout and re-raise as `ConnectionFailedError`
- [ ] 1.7 Run the two adapter test files green

## 2. Connect-failure test double for the TUI

- [ ] 2.1 Add a connect-failure mode to `FakeAdapter` in `tests/fakes.py` (e.g. a `connect_error` that `connect` raises) so the flow tests can drive the error state

## 3. ConnectingModal

- [ ] 3.1 Write failing tests (new `tests/test_tui_connecting.py`): a successful connect dismisses the modal with a session; a raising adapter shows the error state naming the device; Retry after failure re-attempts and succeeds; Cancel dismisses with no session
- [ ] 3.2 Implement `ConnectingModal(ModalScreen)` in `tui/remote_flow.py`: compose `LoadingIndicator` + label + Cancel; `on_mount` starts `run_worker(self._connect(), exclusive=True)`
- [ ] 3.3 Worker: resolve adapter, `await adapter.connect(device)`, `self.dismiss(session)` on success; catch `ConnectionFailedError` and switch to the error state
- [ ] 3.4 Error state: render message naming the device with Retry and Back; Retry restarts the worker in place; Back and Cancel call `self._worker.cancel()` then `self.dismiss(None)`
- [ ] 3.5 Run `tests/test_tui_connecting.py` green

## 4. Wire both connect paths through the modal

- [ ] 4.1 Update `tests/test_tui_remote_flow.py`: stored-credential selection routes through `ConnectingModal` to `RemoteScreen`; after-pairing routes pair → modal → `RemoteScreen`; assert the stack ends without a transient screen under `RemoteScreen`
- [ ] 4.2 `UseRemoteScreen`: in `on_option_list_option_selected`, for a credentialed device push `ConnectingModal(device)` with a callback that pushes `RemoteScreen(session, capabilities, device)` on a non-`None` session; delete `_open_remote` and its inline `await`
- [ ] 4.3 `PairingScreen`: pair and store credential only; `self.dismiss(device)` on success, `self.dismiss(None)` on cancel; remove the inline connect and `switch_screen`
- [ ] 4.4 `UseRemoteScreen`: push `PairingScreen` with a callback that, on a non-`None` device, starts the connect (pushes `ConnectingModal`)
- [ ] 4.5 Run `tests/test_tui_remote_flow.py` green

## 5. Preflight

- [ ] 5.1 `ruff format` and `ruff check --fix`
- [ ] 5.2 Run the full `pytest` suite and fix any regressions
- [ ] 5.3 `openspec validate connecting-loading-spinner --strict`
