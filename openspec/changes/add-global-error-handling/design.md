## Context

The app is a Textual TUI (`textual` 8.2.8). Verified against the installed source: every uncaught path funnels into one method, `App._handle_exception(self, error)` (app.py:3263) — background workers wrap the failure as `WorkerFailed` and call it (worker.py:384), message/event handlers call it (message_pump.py:607/669/691/704), and compose errors reach it too (app.py:3411/3516). Its docstring is explicit: "Always results in the app exiting." It re-raises `self._exception` at shutdown (app.py:2217), which is what surfaces bugs to the pilot/test harness.

Today, each seam catches only its one anticipated domain error and lets the rest propagate to that funnel:
- `ConnectingModal._connect` catches `ConnectionFailedError` only (remote_flow.py:83)
- `PairingScreen._pair` catches `PairingCancelledError` only (remote_flow.py:297)
- `RemoteScreen.on_input_submitted` catches `TextUnsupportedError` only (remote_screen.py:219)
- `RemoteScreen._send` is the one path with a blanket `except Exception` (remote_screen.py:202)
- `UseRemoteScreen._probe_device` wraps `probe` in `try/finally` with no `except` and runs every 5s (remote_flow.py:186, 153)

So user-visible crashes are "anything not on the anticipated list." Adding more one-off `except`s never converges; a single backstop at the funnel does.

## Goals / Non-Goals

**Goals:**
- Unexpected exceptions surface as an error toast and the app stays open.
- Full tracebacks are logged to a file so suppression does not cost debuggability.
- Routinely-flaky seams (probe, discovery) never toast.
- Ctrl-C and normal shutdown are untouched.
- Tests still catch real bugs.

**Non-Goals:**
- Rewriting the Tier-1 seam handlers — their tailored UX stays.
- Making the app survive *every* possible error state (startup/compose errors still exit).
- A user-facing error inbox, error reporting/upload, or crash analytics.
- Changing the `UniversalRemoteError` taxonomy.

## Decisions

### Decision: Override `App._handle_exception` as the single backstop
Catch at the one funnel rather than wrapping every seam. Alternatives considered: (a) a `guard()` decorator on every worker/action — precise but must be remembered for every new seam and misses pure-UI bugs; (b) more per-seam `except Exception` — never converges. The funnel is the only place that catches *everything unexpected* with one change. Trade-off: it is a private method, so the override is pinned to Textual's internals and must be re-checked on upgrade.

### Decision: Expected vs. unexpected split on the `UniversalRemoteError` base
In the override, an error whose (unwrapped) type is a `UniversalRemoteError` is "expected" and carries a user-safe message shown verbatim; anything else is "unexpected" and gets a generic "Something went wrong" toast plus the logged detail. Worker errors arrive wrapped as `WorkerFailed` — unwrap `error.__cause__`/the worker's original error before classifying. In practice most `UniversalRemoteError`s are already caught at their seam and never reach here; the base check is a safety valve for any that slip through.

### Decision: Guard catch-and-stay on app running-state
Only catch-and-stay once the app is running (`self._running` is True — set at app.py:3456/3475). Before that (startup/compose/mount), fall through to Textual's default `_fatal_error`/exit, matching the product decision that a compose/mount error may close the app rather than wedge a half-built tree. This is the simplest robust discriminator between "safe to continue" (runtime worker/handler error) and "structurally broken" (startup).

### Decision: Keep test/pilot bug-surfacing intact
When running under pilot/tests, preserve the `self._exception` bookkeeping (app.py:2217 re-raise) so tests that currently catch bugs via crash still fail. Only the normal-runtime shutdown (`_fatal_error`/`panic`) is skipped in favor of notify-and-stay. Detect the mode the same way Textual does internally (running under a pilot). This keeps the net from silently greening the suite.

### Decision: File logging via stdlib `logging`
Configure a module-level logger writing to a file in the app's state/config directory (co-located with wherever the device store persists). No new dependency. `self.log` is rejected because it targets Textual devtools, not a durable file.

### Decision: Flaky seams handled locally, not at the net
`_probe_device` and the discovery scan are made/confirmed best-effort with a local `except` so failures never propagate to the funnel. This is what keeps the recurring 5s probe from producing a toast storm. The net is reserved for the genuinely unexpected.

## Risks / Trade-offs

- **Private-API override** → Pin to the verified 8.2.8 behavior; add a focused test that drives an in-worker exception through the app and asserts it stays open, so a Textual upgrade that changes the funnel fails loudly.
- **Compose error on a screen *push* while already running** (app running, but the pushed screen half-builds) → the running-state guard treats it as catch-and-stay, so the toast fires but the tree may be partially mounted. Mitigation: acceptable residual — the user stays on the prior screen and can retry or Ctrl-C; document as a known limitation rather than attempt fragile mid-compose detection.
- **Swallowing a bug that recurs** → the app stays open but the same error may re-fire on the next interaction; the file log captures each occurrence for diagnosis, and the user can always quit.
- **Toast on a truly-broken app** → mitigated by the running-state guard (startup errors still exit) and by keeping flaky seams off the net entirely.

## Open Questions

- Exact log file location and rotation policy — reuse the device-store directory; decide whether to cap size. Resolve during implementation (TDD).
- Whether to include a short "see log at <path>" pointer in the generic toast. Lean yes if the path is stable and short.
