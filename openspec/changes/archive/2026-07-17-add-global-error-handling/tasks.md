## 1. Error log file

- [x] 1.1 Write a failing test: a `default_log_path()` returns `$XDG_CONFIG_HOME/universal-remote/error.log`, falling back to `~/.config/...`, mirroring `default_store_path()`
- [x] 1.2 Write a failing test: logging an exception appends its type, message, and full traceback to the log file
- [x] 1.3 Implement the file logger (stdlib `logging`, module-level, writing to `default_log_path()`); create the parent dir like the store does
- [x] 1.4 Confirm tests 1.1–1.2 pass

## 2. Global net on the app

- [x] 2.1 Write a failing test driving an in-worker exception through a running app: the app stays open (not exited) and an error-severity toast is posted
- [x] 2.2 Write a failing test: a screen-level message-handler exception while running is caught-and-stayed with a toast (an app-pump binding action, by contrast, still tears down — see design residual)
- [x] 2.3 Write a failing test: the caught exception's full traceback is written to the log file
- [x] 2.4 Override `UniversalRemoteApp._handle_exception(self, error)`: when `self._running` is True, log the traceback, post an error toast via `self.notify(..., severity="error")`, and return without exiting
- [x] 2.5 Unwrap `WorkerFailed` to the original error before classifying; classify `UniversalRemoteError` as expected (show its message verbatim) vs. unexpected (generic "Something went wrong" message)
- [x] 2.6 Confirm tests 2.1–2.3 pass
- [x] 2.7 Write a failing test (unwritable log dir) then wrap the net's log+notify body so a failure in the net's own reporting can never itself crash the app; still record `self._exception` afterward. Do not set a non-zero return code for a recovered error

## 3. App-closing and pass-through guards

- [x] 3.1 Write a failing test: an exception raised before the app is running (startup/compose/mount) still causes the app to exit
- [x] 3.2 Write a failing test: under the pilot/test harness, `self._exception` is still set so bugs surface (the suite still catches them)
- [x] 3.3 In the override, fall through to the default `_fatal_error`/exit path when the app is not yet mounted (`self._is_mounted` is False), and preserve the `self._exception` bookkeeping (set unconditionally; `run()` never re-raises it, `run_test()` does)
- [x] 3.4 Verify `KeyboardInterrupt`/`SystemExit`/`asyncio.CancelledError` are `BaseException` and never reach the hook (message pump catches `except Exception` and re-raises `CancelledError`); Ctrl-C unaffected — verified by code reading, an explicit test is impractical
- [x] 3.5 Confirm tests 3.1–3.2 pass

## 4. Flaky seams stay off the net

- [x] 4.1 Write a failing test: a failing reachability probe produces no toast and leaves siblings unaffected
- [x] 4.2 Add a local `except` in `UseRemoteScreen._probe_device` so a probe failure/timeout never propagates to the funnel (row stays unknown/unreachable, no toast)
- [x] 4.3 Confirm `discover_one` already isolates per-adapter scan failures; add a test asserting a failing scan yields no toast, and tighten the seam if it can leak
- [x] 4.4 Confirm tests 4.1–4.3 pass
- [x] 4.5 Tier-1 hardening: give `RemoteScreen.on_input_submitted` the same broad `except` as `_send`, so an unexpected `send_text` failure shows a status and keeps the screen alive instead of freezing its pump (test in `test_tui_remote_surface.py`)

## 5. Documentation and preflight

- [x] 5.1 Update in-repo docs if any reference error/crash behavior (README or module docstrings) to note the new net and log file location
- [x] 5.2 Preflight: run the formatter, fix lint/analysis issues, run the full test suite; address failures
- [x] 5.3 Manually verify: trigger a forced unexpected error in a running app and confirm the toast shows, the app stays open, and the traceback lands in the log file (verified on the prod `run_async` path — no re-raise, no terminal traceback, toast shown, `error.log` written)
