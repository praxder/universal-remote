## 1. Reachability module

- [ ] 1.1 Write `tests/test_reachability.py`: probe returns REACHABLE when a local listening socket accepts the connection
- [ ] 1.2 Extend `tests/test_reachability.py`: probe returns UNREACHABLE on refused connection, on timeout (no accept within the bound), and on OSError
- [ ] 1.3 Implement `src/universal_remote/reachability.py`: a `Reachability` enum (REACHABLE, UNREACHABLE, UNKNOWN) and `async def probe(ip, port, timeout) -> Reachability` using `asyncio.wait_for(asyncio.open_connection(...), timeout)`, closing the transport on success
- [ ] 1.4 Confirm the module has no imports from `adapters` or `tui` (keep it standalone and app-free)

## 2. Per-adapter reachability port

- [ ] 2.1 Add `reachability_port` to each adapter class: Samsung 8002, Roku 8060, Fire TV 5555, LG 3000, Android TV 6466, Apple TV 7000
- [ ] 2.2 Add/extend each adapter test (`tests/test_<platform>_adapter.py`) to assert the adapter exposes the expected `reachability_port`
- [ ] 2.3 Verify `getattr(adapter, "reachability_port", None)` yields `None` for an adapter that declares none (no code change; a guard test in `tests/test_reachability.py` or a registry test)

## 3. Use Remote picker indicator

- [ ] 3.1 Write picker tests in `tests/test_tui_remote_flow.py`: on opening Use Remote, every device row renders immediately with a yellow bubble positioned before its `N.` number, before any probe resolves
- [ ] 3.2 Extend tests: a device whose probe resolves REACHABLE shows a green bubble and one that resolves UNREACHABLE shows red, each updated in place (highlight/cursor preserved), driven by a fake probe
- [ ] 3.3 Extend tests: a device on an adapter with no `reachability_port` stays yellow
- [ ] 3.4 Extend tests: selecting a red-bubble device still begins the connect/pair flow (indicator is advisory)
- [ ] 3.5 Extend tests: the polling interval triggers a re-probe while open, and no probe is started after the screen is left
- [ ] 3.6 Implement bubble rendering in `UseRemoteScreen.on_mount` (`remote_flow.py`): render each row with a yellow Rich-markup `●` before the number; map REACHABLE/UNREACHABLE/UNKNOWN → green/red/yellow markup
- [ ] 3.7 Implement the probe cycle: resolve each device's adapter port, probe devices with a port concurrently (timeout 2.0s), leave portless devices yellow, and update each row in place via `replace_option_prompt_at_index` as results resolve
- [ ] 3.8 Implement interval polling: run one cycle immediately, then `set_interval(5.0, ...)`; add a per-device in-flight guard so a slow probe does not stack; stop the interval and cancel in-flight work on unmount / leaving the screen

## 4. Docs, preflight, and verification

- [ ] 4.1 Update `README.md` to mention the reachability indicator in the Use Remote / Pair-and-control section
- [ ] 4.2 Run the formatter and linter (`uv run ruff format`, `uv run ruff check`) and fix findings
- [ ] 4.3 Run the full test suite (`uv run pytest`) and confirm all tests pass
- [ ] 4.4 Launch the app (`uv run universal-remote`) and confirm bubbles render and refresh in the Use Remote picker
