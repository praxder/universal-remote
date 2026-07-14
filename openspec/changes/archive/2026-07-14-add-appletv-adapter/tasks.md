## 1. Dependency

- [x] 1.1 Add `pyatv` to `pyproject.toml` dependencies and run `uv sync`
- [x] 1.2 Confirm the installed `pyatv` entry points against the pinned version (resolves design's open questions): `scan(loop, hosts=[…])`, the pairing object (`begin`/`device_provides_pin`/`pin`/`finish`/`has_paired`/`service.credentials`/`close`), `connect(config, loop)`, `set_credentials`, `remote_control` methods for nav/select/menu/home, `audio.volume_up`/`volume_down` for volume (RemoteControl volume is deprecated), and the keyboard interface (`text_set`/`text_append`) for text

## 2. Device model gains a reconnection identifier (TDD)

- [x] 2.1 Extend `tests/test_store.py` (red): a device saved with an `identifier` round-trips it on load; a device without one loads with `identifier` as `None`; an existing store file with no `identifier` key still loads
- [x] 2.2 Add `identifier: str | None = None` to `Device` in `devices/models.py` (green); confirm `to_dict`/`from_dict` need no other change
- [x] 2.3 Ensure `tests/test_store.py` and `tests/test_device_crud.py` pass

## 3. Apple TV adapter (TDD)

- [x] 3.1 Add a fake `pyatv` double to `tests/fakes.py`: records scanned hosts, drives a two-phase pairing (begin → provides PIN → accepts a `pin(value)` → finishes with credentials), verifies identity on connect, and records dispatched remote-control methods and text; configurable to fail connect and to reject text
- [x] 3.2 Write `tests/test_appletv_adapter.py` (red): platform id `apple-tv` resolves; display name is "Apple TV"; capabilities include the directional keys, OK, back, home, and volume, exclude MUTE, and declare `text=True`; `pair()` with a prompt drives begin → prompts for the PIN → submits it → returns the Companion credential and records the identifier on the device; `pair()` with `prompt=None` raises `PairingCancelledError`; `connect()` scans the stored IP, rejects an identifier mismatch with `ConnectionFailedError`, and on match applies the credential and returns a session; each generic key dispatches to the correct `pyatv` method; text failure raises `TextUnsupportedError`
- [x] 3.3 Implement `src/universal_remote/adapters/appletv.py`: key→method mapping, `AppleTvSession(BaseSession)` with `_dispatch_key`/`_dispatch_text`/`_release`, `AppleTvAdapter` (`platform`, `display_name`, `capabilities`, `pair`, `connect`), injected `pyatv` factory, and `register(registry)` (green)
- [x] 3.4 Refactor for parity with `adapters/lg.py` and `adapters/samsung.py`; ensure `tests/test_appletv_adapter.py` passes

## 4. Register the adapter

- [x] 4.1 Extend `tests/test_cli_integration.py` (red): after `build_app`, the registry resolves `apple-tv`
- [x] 4.2 Wire `register_appletv` into `cli.build_app` alongside the existing adapters (green)

## 5. PIN entry in the pairing flow (TDD)

- [x] 5.1 Extend `tests/test_pairing.py` / `tests/test_tui_remote_flow.py` (red): when the adapter requests a value during pairing, `PairingScreen` shows a PIN-entry state with the adapter's message and an input; submitting the value resolves the adapter's `prompt` and pairing completes, storing credential and identifier; cancelling during the PIN prompt dismisses without storing; an adapter that never prompts (existing fake) pairs exactly as before
- [x] 5.2 Add the prompt bridge to `PairingScreen` in `tui/remote_flow.py`: pass a bound `prompt` coroutine to `adapter.pair(...)`; on `prompt(message)` swap to a PIN-entry state (message + `Input` + Submit) and resolve via an `asyncio.Future`; make guidance adapter-driven; keep Esc/Cancel cancellation behaviour (green)
- [x] 5.3 Refactor; ensure all pairing and remote-flow tests pass

## 6. Documentation & preflight

- [x] 6.1 Update `README.md`: note Apple TV support, that pairing shows a PIN on the TV to type into the app, and that MUTE is unavailable on Apple TV
- [x] 6.2 Run `uv run ruff format` and `uv run ruff check`
- [x] 6.3 Run `uv run pytest` — full suite green
