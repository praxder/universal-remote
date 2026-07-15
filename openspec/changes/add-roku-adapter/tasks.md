## 1. Dependency

- [ ] 1.1 Add `rokuecp` to `pyproject.toml` dependencies and run `uv sync`
- [ ] 1.2 Confirm the installed `rokuecp` entry points against the pinned version (resolves design's open questions): the `Roku` client constructor and how the `aiohttp` session is supplied, the button-press method and its accepted ECP key vocabulary (`Up`/`Down`/`Left`/`Right`/`Select`/`Back`/`Home`/`VolumeUp`/`VolumeDown`/`VolumeMute`/`ChannelUp`/`ChannelDown`/`Play`/`Rev`/`Fwd`), the literal-text method, the device-info/reachability method, and the error types raised on failure

## 2. Roku adapter (TDD)

- [ ] 2.1 Add a fake `rokuecp` double to `tests/fakes.py`: records the ECP session it was built for, records dispatched button-press keys and literal text, answers a reachability/device-info call, and is configurable to fail the reachability check and to reject text
- [ ] 2.2 Write `tests/test_roku_adapter.py` (red): platform id `roku` resolves; display name is "Roku"; `requires_pairing` is `False`; capabilities include the directional keys, OK, back, home, volume up/down, mute, channel up/down, play/pause, rewind, and fast-forward, exclude discrete play/pause/stop, the number-pad digits, and menu, and declare `text=True`; `pair()` raises `PairingCancelledError` (Roku needs no pairing); `connect()` builds a client for the stored IP, reports `ConnectionFailedError` when the reachability check fails, and returns a session on success; each supported generic key dispatches to the correct ECP key; play/pause dispatches Roku's single toggle; an unsupported key raises `UnsupportedKeyError`; text dispatches as literal characters and text failure raises `TextUnsupportedError`
- [ ] 2.3 Implement `src/universal_remote/adapters/roku.py`: key→ECP mapping, `RokuSession(BaseSession)` with `_dispatch_key`/`_dispatch_text`/`_release` (closing the owned `aiohttp` session), `RokuAdapter` (`platform`, `display_name`, `requires_pairing = False`, `capabilities`, `pair` raising `PairingCancelledError`, `connect` with reachability check), an injected `rokuecp`/session factory, and `register(registry)` (green)
- [ ] 2.4 Refactor for parity with `adapters/lg.py`, `adapters/samsung.py`, and `adapters/appletv.py`; ensure `tests/test_roku_adapter.py` passes

## 3. Register the adapter

- [ ] 3.1 Extend `tests/test_cli_integration.py` (red): after `build_app`, the registry resolves `roku`
- [ ] 3.2 Wire `register_roku` into `cli.build_app` alongside the existing adapters (green)

## 4. Skip pairing for a no-pairing adapter (TDD)

- [ ] 4.1 Give `FakeAdapter` in `tests/fakes.py` a `requires_pairing` attribute defaulting to `True`, settable to `False`
- [ ] 4.2 Extend `tests/test_tui_remote_flow.py` (red): a credential-less device whose adapter has `requires_pairing = False` connects directly via `ConnectingModal` and never mounts `PairingScreen`; a credential-less device whose adapter requires pairing still runs `PairingScreen` exactly as before; an adapter that declares nothing defaults to requiring pairing
- [ ] 4.3 In `tui/remote_flow.py`, gate the pairing branch of `UseRemoteScreen` on `getattr(adapter, "requires_pairing", True)`, resolving the adapter before the branch and connecting directly when it needs no pairing (green)
- [ ] 4.4 Add a comment to `adapter.py` documenting the optional `requires_pairing` convention (default `True`); ensure all pairing and remote-flow tests pass

## 5. Documentation & preflight

- [ ] 5.1 Update `README.md`: note Roku support, that Roku needs no pairing (connects directly, manual IP entry), and which keys are unavailable on Roku (discrete play/pause/stop, number pad, menu)
- [ ] 5.2 Run `uv run ruff format` and `uv run ruff check`
- [ ] 5.3 Run `uv run pytest` — full suite green
