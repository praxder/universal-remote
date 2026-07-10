## 1. Dependency

- [x] 1.1 Add `aiowebostv` to `pyproject.toml` dependencies and run `uv sync`
- [x] 1.2 Confirm the LG client's pairing, input-channel send, and SSAP request entry points against the installed version (resolves the design's open questions)

## 2. LG WebOS adapter (TDD)

- [x] 2.1 Add a fake LG transport to `tests/fakes.py` mirroring the fake Samsung remote (records sent keys/text, returns a client-key on pair, raises on text when configured)
- [x] 2.2 Write `tests/test_lg_adapter.py` (red): platform id resolves; capabilities include the 11 keys with text and power-on flags; pair returns a client-key; connect replays a stored client-key without prompting; each generic key dispatches to the correct mechanism (input channel vs SSAP); text failure raises `TextUnsupportedError`; power-on with a MAC sends WoL and reports best-effort, without a MAC reports not sent
- [x] 2.3 Implement `src/universal_remote/adapters/lg.py`: `LG_BUTTONS` mapping, `LgWebOsSession(BaseSession)` with `_dispatch_key`/`_dispatch_text`/`_release`, `LgWebOsAdapter` (`platform`, `capabilities`, `pair`, `connect`, `power_on`), injected client factory + WoL callable, and `register(registry)` (green)
- [x] 2.4 Refactor for parity with `adapters/samsung.py`; ensure `tests/test_lg_adapter.py` passes

## 3. Register the adapter

- [x] 3.1 Extend `tests/test_cli_integration.py` (red): after `build_app`, the registry resolves `lg-webos`
- [x] 3.2 Wire `register_lg` into `cli.build_app` alongside `register_samsung` (green)

## 4. Platform selector in Add-Device (TDD)

- [x] 4.1 Extend `tests/test_tui_devices.py` (red): with two adapters registered, adding a device shows a platform selector defaulting to the first and saves the selected platform; with one adapter registered, no selector is shown and the sole platform is assigned
- [x] 4.2 Add a `Select` of `registry.platforms()` to `AddDeviceScreen`, shown only when more than one platform is registered, defaulting to the first; store the chosen platform on the saved `Device`; keep edit behavior unchanged (green)
- [x] 4.3 Refactor; ensure TUI device tests pass

## 5. Documentation & preflight

- [x] 5.1 Update `README.md`: note LG WebOS support and that platform is chosen when adding a device; note LG uses manual entry (no probe auto-fill)
- [x] 5.2 Run `uv run ruff format` and `uv run ruff check`
- [x] 5.3 Run `uv run pytest` — full suite green
