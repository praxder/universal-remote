## 1. Project scaffold

- [x] 1.1 Initialize project with `uv`; create `pyproject.toml` and pin Python 3.13 (`.python-version`)
- [x] 1.2 Add runtime deps (`textual`, `samsungtvws`, `wakeonlan`) and dev dep (`pytest`); run `uv sync` and confirm resolution on 3.13
- [x] 1.3 Create `src/universal_remote/` package layout (`devices/`, `adapters/`, `tui/`, `cli.py`) and `tests/`
- [x] 1.4 Add a console-script entry point that launches the Textual app; verify `uv run universal-remote` starts and exits cleanly

## 2. Remote-control core (the seam)

- [x] 2.1 Write tests for the generic `Key` vocabulary (up/down/left/right/OK/back/home/vol±/mute/power) and `Capabilities` (declared keys + text/power-on flags) — red
- [x] 2.2 Implement `Key` enum and `Capabilities` — green
- [x] 2.3 Write tests for the adapter registry: known platform resolves, unknown platform reported unsupported — red
- [x] 2.4 Implement `Adapter`/`Session` Protocols and the registry — green
- [x] 2.5 Build a `FakeAdapter`/`FakeSession` test double (records sent keys/text, configurable capabilities, scriptable pair result)
- [x] 2.6 Write tests for session behavior via `FakeAdapter`: supported key dispatches, unsupported key rejected (no substitute), close releases and further sends fail — red
- [x] 2.7 Implement session-level capability gating so unsupported keys are rejected before dispatch — green
- [x] 2.8 Write tests for pairing lifecycle: pairing yields a persistable credential, cancellation persists nothing and reports cancelled — red/green

## 3. Device management

- [x] 3.1 Write tests for the JSON store: create-on-first-save with mode `0600`, credential round-trip, empty list, multi-device list — red
- [x] 3.2 Implement the XDG-aware store (`~/.config/universal-remote/devices.json`, `0600`) and device model — green
- [x] 3.3 Write tests for CRUD: add, edit persists, delete removes only the target — red
- [x] 3.4 Implement device CRUD over the store — green
- [x] 3.5 Write tests for IP auto-fill: probe success prefills name/model/MAC; probe failure degrades to manual without blocking add (probe mocked) — red
- [x] 3.6 Implement the info-probe auto-fill helper (`GET http://<ip>:8001/api/v2/`, mockable transport) — green

## 4. Samsung Tizen adapter

- [x] 4.1 Write tests with a mocked `samsungtvws` transport: adapter registers under its platform id and declares the core button set — red
- [x] 4.2 Implement adapter registration and `capabilities()` — green
- [x] 4.3 Write tests for token pairing (first pair returns token; stored token reused without popup) and key mapping (generic → Samsung code) against the mock — red
- [x] 4.4 Implement async pairing, connect-with-token, and key mapping — green
- [x] 4.5 Write tests for best-effort text (failure/unsupported reported, not silently dropped) and power (off = power key; on = WOL to stored MAC, flagged best-effort) — red
- [x] 4.6 Implement text send with unsupported reporting and power handling (WOL via `wakeonlan`) — green

## 5. TUI (Textual)

- [x] 5.1 Write tests (Textual test harness) for the entry menu: both modes present and selectable by key and by click — red
- [x] 5.2 Implement the menu app and navigation — green
- [x] 5.3 Write tests for device screens: list renders saved devices; add flow reaches IP-entry/confirm and saves (store + probe faked) — red
- [x] 5.4 Implement device management screens wired to the store — green
- [x] 5.5 Write tests for Use Remote entry: select among multiple devices; zero devices guides to add; stored credential connects directly; no credential runs a cancellable pairing step; exit returns to menu (store + `FakeAdapter` faked) — red
- [x] 5.6 Implement the Use Remote entry flow: device selection → pair-if-needed (on-screen guidance, cancellable) → connect → exit-to-menu — green
- [x] 5.7 Write tests for the remote surface: full button set renders; click sends the mapped key; arrows/Enter/Esc/Home map to keys via a `FakeAdapter` — red
- [x] 5.8 Implement the remote screen (buttons + keyboard bindings) against the adapter session — green
- [x] 5.9 Write tests for capability-driven disabling and text-entry focus behavior (compose-then-send; Esc exits field without Back; text-unsupported disables field) — red
- [x] 5.10 Implement capability gating in the UI and the text-entry focus model — green

## 6. Integration and preflight

- [x] 6.1 Wire `cli.py` end to end: menu → device mgmt / device pick → remote, using the registry to resolve adapters
- [x] 6.2 Register the Samsung adapter with the core registry at startup
- [x] 6.3 Add a short README (run, add a Samsung TV, pair, control) noting best-effort text and power-on caveats
- [x] 6.4 Preflight: format, lint, and run the full `pytest` suite green with no real-TV dependency
- [x] 6.5 Manual smoke test against a real Samsung Tizen TV (pair popup, D-pad, volume, power-off, text attempt); record firmware text-input behavior — **BLOCKED: requires real Samsung Tizen hardware; cannot run in this environment.**

  Everything above is unit-tested against `FakeSamsungRemote`/`FakeAdapter` and a mocked transport only. The seams below have never touched a real TV — verify each on hardware:
  - **Token round-trip** (never run): first connect with no token must trigger the on-TV popup and, on accept, populate `remote.token` (see `SamsungTizenAdapter.pair`); a saved token must reconnect via `connect` with no popup. This is the load-bearing pairing path.
  - **Text input** on the set's firmware: does the text field actually type? Record the behavior (works / silently drops / errors) — drives the best-effort text decision (design risk).
  - **Power**: power-off via the `POWER` button (`KEY_POWER`) while connected should work; WOL power-on (`adapter.power_on`) needs the TV's "Network Standby / Wake on LAN" setting enabled or it silently no-ops.
  - **Pairing wait**: `_PAIR_TIMEOUT` is the websocket handshake `open_timeout`; the event-read loop itself is unbounded, so a pending popup blocks the pairing worker until the user cancels — the Cancel/Esc path is the escape hatch. Confirm cancel works on hardware.
