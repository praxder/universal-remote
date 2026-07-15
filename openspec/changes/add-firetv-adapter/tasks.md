## 1. Dependency

- [ ] 1.1 Add `adb-shell` to `pyproject.toml` dependencies and run `uv sync`
- [ ] 1.2 Confirm the installed `adb-shell` entry points against the pinned version (resolves design's open questions): the async TCP device class and constructor (`AdbDeviceTcpAsync(host, port)`), keypair generation and signer construction (`keygen`, `PythonRSASigner`), the `connect(rsa_keys=..., auth_timeout_s=...)` signature and what a fresh-pair vs credential-replay connect returns, the `shell(cmd)` and `close()` methods, the ADB key-event codes for the declared keys, and the error/timeout types raised on failure; confirm the keygen private-key output is directly loadable back into a `PythonRSASigner`

## 2. Fire TV adapter (TDD)

- [ ] 2.1 Add a fake `adb-shell` double to `tests/fakes.py`: records the host/port it was built for, records `connect(rsa_keys=..., auth_timeout_s=...)` calls (distinguishing pair-time vs connect-time), records dispatched `shell` commands (`input keyevent <code>` / `input text <str>`), is configurable to fail the connect handshake and to reject text, and exposes a keygen/signer stand-in so `pair()` can produce a deterministic credential
- [ ] 2.2 Write `tests/test_firetv_adapter.py` (red): platform id `firetv` resolves; display name is "Fire TV"; `requires_pairing` is `True` (or unset, defaulting True); capabilities include the directional keys, OK, back, home, menu, volume up/down, mute, discrete play/pause/stop, play/pause, rewind, fast-forward, and the number-pad digits, exclude channel up/down, and declare `text=True`; `pair()` generates a keypair, connects (triggering the popup), returns a private-key PEM credential, and never calls `prompt`; `connect()` rebuilds the signer from the stored credential, connects to the stored IP on port 5555, reports `ConnectionFailedError` when the handshake fails, and returns a session on success; each supported generic key dispatches the correct `input keyevent <code>` command; an unsupported key raises `UnsupportedKeyError`; text dispatches as `input text <str>` and text failure raises `TextUnsupportedError`
- [ ] 2.3 Implement `src/universal_remote/adapters/firetv.py`: key→ADB-key-event mapping, `FireTvSession(BaseSession)` with `_dispatch_key`/`_dispatch_text`/`_release` (closing the ADB connection it owns), `FireTvAdapter` (`platform`, `display_name`, `capabilities`, `pair` generating and returning the PEM, `connect` replaying the stored PEM with a reachability handshake), injected `adb-shell` device/keygen factories, and `register(registry)` (green)
- [ ] 2.4 Refactor for parity with `adapters/roku.py`, `adapters/appletv.py`, `adapters/lg.py`, and `adapters/samsung.py`; ensure the signer is always built from the in-memory per-device PEM (never `~/.android/adbkey`); ensure `tests/test_firetv_adapter.py` passes

## 3. Register the adapter

- [ ] 3.1 Extend `tests/test_cli_integration.py` (red): after `build_app`, the registry resolves `firetv`
- [ ] 3.2 Wire `register_firetv` into `cli.build_app` alongside the existing adapters (green)

## 4. Documentation & preflight

- [ ] 4.1 Update `README.md`: add Fire TV to the platform list; note the Developer Options → ADB debugging prerequisite; note that pairing is the standard authorization-popup flow (accept on the TV, tick "Always allow from this computer" so later connections skip the dialog); note that channel up/down are unavailable on Fire TV
- [ ] 4.2 Run `uv run ruff format` and `uv run ruff check`
- [ ] 4.3 Run `uv run pytest` — full suite green
