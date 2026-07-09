## 1. Project scaffold

- [ ] 1.1 Initialize project with `uv`; create `pyproject.toml` and pin Python 3.13 (`.python-version`)
- [ ] 1.2 Add runtime deps (`textual`, `samsungtvws`, `wakeonlan`) and dev dep (`pytest`); run `uv sync` and confirm resolution on 3.13
- [ ] 1.3 Create `src/universal_remote/` package layout (`devices/`, `adapters/`, `tui/`, `cli.py`) and `tests/`
- [ ] 1.4 Add a console-script entry point that launches the Textual app; verify `uv run universal-remote` starts and exits cleanly

## 2. Remote-control core (the seam)

- [ ] 2.1 Write tests for the generic `Key` vocabulary (up/down/left/right/OK/back/home/vol±/mute/power) and `Capabilities` (declared keys + text/power-on flags) — red
- [ ] 2.2 Implement `Key` enum and `Capabilities` — green
- [ ] 2.3 Write tests for the adapter registry: known platform resolves, unknown platform reported unsupported — red
- [ ] 2.4 Implement `Adapter`/`Session` Protocols and the registry — green
- [ ] 2.5 Build a `FakeAdapter`/`FakeSession` test double (records sent keys/text, configurable capabilities, scriptable pair result)
- [ ] 2.6 Write tests for session behavior via `FakeAdapter`: supported key dispatches, unsupported key rejected (no substitute), close releases and further sends fail — red
- [ ] 2.7 Implement session-level capability gating so unsupported keys are rejected before dispatch — green
- [ ] 2.8 Write tests for pairing lifecycle: pairing yields a persistable credential, cancellation persists nothing and reports cancelled — red/green

## 3. Device management

- [ ] 3.1 Write tests for the JSON store: create-on-first-save with mode `0600`, credential round-trip, empty list, multi-device list — red
- [ ] 3.2 Implement the XDG-aware store (`~/.config/universal-remote/devices.json`, `0600`) and device model — green
- [ ] 3.3 Write tests for CRUD: add, edit persists, delete removes only the target — red
- [ ] 3.4 Implement device CRUD over the store — green
- [ ] 3.5 Write tests for IP auto-fill: probe success prefills name/model/MAC; probe failure degrades to manual without blocking add (probe mocked) — red
- [ ] 3.6 Implement the info-probe auto-fill helper (`GET http://<ip>:8001/api/v2/`, mockable transport) — green

## 4. Samsung Tizen adapter

- [ ] 4.1 Write tests with a mocked `samsungtvws` transport: adapter registers under its platform id and declares the core button set — red
- [ ] 4.2 Implement adapter registration and `capabilities()` — green
- [ ] 4.3 Write tests for token pairing (first pair returns token; stored token reused without popup) and key mapping (generic → Samsung code) against the mock — red
- [ ] 4.4 Implement async pairing, connect-with-token, and key mapping — green
- [ ] 4.5 Write tests for best-effort text (failure/unsupported reported, not silently dropped) and power (off = power key; on = WOL to stored MAC, flagged best-effort) — red
- [ ] 4.6 Implement text send with unsupported reporting and power handling (WOL via `wakeonlan`) — green

## 5. TUI (Textual)

- [ ] 5.1 Write tests (Textual test harness) for the entry menu: both modes present and selectable by key and by click — red
- [ ] 5.2 Implement the menu app and navigation — green
- [ ] 5.3 Write tests for device screens: list renders saved devices; add flow reaches IP-entry/confirm and saves (store + probe faked) — red
- [ ] 5.4 Implement device management screens wired to the store — green
- [ ] 5.5 Write tests for Use Remote entry: select among multiple devices; zero devices guides to add; stored credential connects directly; no credential runs a cancellable pairing step; exit returns to menu (store + `FakeAdapter` faked) — red
- [ ] 5.6 Implement the Use Remote entry flow: device selection → pair-if-needed (on-screen guidance, cancellable) → connect → exit-to-menu — green
- [ ] 5.7 Write tests for the remote surface: full button set renders; click sends the mapped key; arrows/Enter/Esc/Home map to keys via a `FakeAdapter` — red
- [ ] 5.8 Implement the remote screen (buttons + keyboard bindings) against the adapter session — green
- [ ] 5.9 Write tests for capability-driven disabling and text-entry focus behavior (compose-then-send; Esc exits field without Back; text-unsupported disables field) — red
- [ ] 5.10 Implement capability gating in the UI and the text-entry focus model — green

## 6. Integration and preflight

- [ ] 6.1 Wire `cli.py` end to end: menu → device mgmt / device pick → remote, using the registry to resolve adapters
- [ ] 6.2 Register the Samsung adapter with the core registry at startup
- [ ] 6.3 Add a short README (run, add a Samsung TV, pair, control) noting best-effort text and power-on caveats
- [ ] 6.4 Preflight: format, lint, and run the full `pytest` suite green with no real-TV dependency
- [ ] 6.5 Manual smoke test against a real Samsung Tizen TV (pair popup, D-pad, volume, power-off, text attempt); record firmware text-input behavior
