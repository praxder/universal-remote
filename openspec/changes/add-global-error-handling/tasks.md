## 1. Error log file

- [ ] 1.1 Write a failing test: a `default_log_path()` returns `$XDG_CONFIG_HOME/universal-remote/error.log`, falling back to `~/.config/...`, mirroring `default_store_path()`
- [ ] 1.2 Write a failing test: logging an exception appends its type, message, and full traceback to the log file
- [ ] 1.3 Implement the file logger (stdlib `logging`, module-level, writing to `default_log_path()`); create the parent dir like the store does
- [ ] 1.4 Confirm tests 1.1–1.2 pass

## 2. Global net on the app

- [ ] 2.1 Write a failing test driving an in-worker exception through a running app: the app stays open (not exited) and an error-severity toast is posted
- [ ] 2.2 Write a failing test: a message-handler exception while running is caught-and-stayed with a toast
- [ ] 2.3 Write a failing test: the caught exception's full traceback is written to the log file
- [ ] 2.4 Override `UniversalRemoteApp._handle_exception(self, error)`: when `self._running` is True, log the traceback, post an error toast via `self.notify(..., severity="error")`, and return without exiting
- [ ] 2.5 Unwrap `WorkerFailed` to the original error before classifying; classify `UniversalRemoteError` as expected (show its message verbatim) vs. unexpected (generic "Something went wrong" message)
- [ ] 2.6 Confirm tests 2.1–2.3 pass

## 3. App-closing and pass-through guards

- [ ] 3.1 Write a failing test: an exception raised before the app is running (startup/compose/mount) still causes the app to exit
- [ ] 3.2 Write a failing test: under the pilot/test harness, `self._exception` is still set so bugs surface (the suite still catches them)
- [ ] 3.3 In the override, fall through to the default `_fatal_error`/exit path when `self._running` is False, and preserve the `self._exception` bookkeeping under pilot/test mode
- [ ] 3.4 Verify `KeyboardInterrupt`/`SystemExit`/`asyncio.CancelledError` are `BaseException` and never reach the hook (assert Ctrl-C is unaffected); add a test if practical
- [ ] 3.5 Confirm tests 3.1–3.2 pass

## 4. Flaky seams stay off the net

- [ ] 4.1 Write a failing test: a failing reachability probe produces no toast and leaves siblings unaffected
- [ ] 4.2 Add a local `except` in `UseRemoteScreen._probe_device` so a probe failure/timeout never propagates to the funnel (row stays unknown/unreachable, no toast)
- [ ] 4.3 Confirm `discover_one` already isolates per-adapter scan failures; add a test asserting a failing scan yields no toast, and tighten the seam if it can leak
- [ ] 4.4 Confirm tests 4.1–4.3 pass

## 5. Documentation and preflight

- [ ] 5.1 Update in-repo docs if any reference error/crash behavior (README or module docstrings) to note the new net and log file location
- [ ] 5.2 Preflight: run the formatter, fix lint/analysis issues, run the full test suite; address failures
- [ ] 5.3 Manually verify: trigger a forced unexpected error in a running app and confirm the toast shows, the app stays open, and the traceback lands in the log file
