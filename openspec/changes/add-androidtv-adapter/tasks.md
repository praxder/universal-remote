## 1. Dependency

- [ ] 1.1 Add `androidtvremote2` to `pyproject.toml` dependencies and run `uv sync`
- [ ] 1.2 Confirm the installed library's entry points and key table against the pinned version (resolves design's open questions): `AndroidTVRemote(client_name, certfile, keyfile, host)`, `async_generate_cert_if_missing()`, `async_start_pairing()`, `async_finish_pairing(code)`, `async_connect()`, `disconnect()`, `send_key_command(name)`, `send_text(text)`, and the exact fully-prefixed `KEYCODE_*` names accepted. Also confirm: (a) the pairing **sequence** — whether pairing must be triggered by/after a connect attempt (library may raise `InvalidAuth` on connect, then pair), which stays encapsulated inside `pair()`; (b) that `send_text` rests on the constructor's `enable_ime=True` and the adapter does not disable it, so the declared `text=True` capability actually functions; (c) whether `certfile`/`keyfile` are re-read after `async_connect`

## 2. Android TV adapter (TDD)

- [ ] 2.1 Add a fake `androidtvremote2` double to `tests/fakes.py`: records the constructed host/cert/key, drives pairing (start → accepts a `finish(code)`), records the connect call and can be configured to fail it, and records dispatched key commands and text (configurable to reject text)
- [ ] 2.2 Write `tests/test_androidtv_adapter.py` (red): platform id `androidtv` resolves; display name is "Android TV"; capabilities include the directional keys, OK, back, home, menu, volume, mute, channel up/down, the media-transport keys, and the digits, and declare `text=True`; `pair()` with a prompt drives start → prompts for the code → submits it → returns a credential packing the cert and key; `pair()` with `prompt=None` raises `PairingCancelledError`; `connect()` materializes the credential, connects, returns a session, and maps a library connect failure to `ConnectionFailedError`; each generic key dispatches the correct `send_key_command` argument; text failure raises `TextUnsupportedError`
- [ ] 2.3 Implement `src/universal_remote/adapters/androidtv.py`: `KEYCODE_*` key mapping, credential pack/unpack helpers, the temp-dir cert bridge for pair and connect, `AndroidTvSession(BaseSession)` with `_dispatch_key`/`_dispatch_text`/`_release` (removes the temp dir), `AndroidTvAdapter` (`platform`, `display_name`, `capabilities`, `pair`, `connect`), injected library factory, and `register(registry)` (green)
- [ ] 2.4 Refactor for parity with `adapters/appletv.py`; ensure `tests/test_androidtv_adapter.py` passes

## 3. Register the adapter

- [ ] 3.1 Extend `tests/test_cli_integration.py` (red): after `build_app`, the registry resolves `androidtv`
- [ ] 3.2 Wire `register_androidtv` into `cli.build_app` alongside the existing adapters (green)

## 4. Documentation & preflight

- [ ] 4.1 Update `README.md`: note Android TV / Google TV support and that pairing shows a code on the TV to type into the app
- [ ] 4.2 Run `uv run ruff format` and `uv run ruff check`
- [ ] 4.3 Run `uv run pytest` — full suite green
