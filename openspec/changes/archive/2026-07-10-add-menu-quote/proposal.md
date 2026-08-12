## Why

The entry menu is functional but bare — a banner and two buttons. A rotating famous movie/TV quote adds personality and a small moment of delight on every launch, at essentially zero cost and no new dependencies.

## What Changes

- The landing menu (`MenuScreen`) displays one famous movie/TV quote with attribution beneath the two mode buttons.
- Attribution reads `— character, source` (e.g. `— Darth Vader, Star Wars`).
- Quotes are stored in a packaged text file, one per line as `text|character|source`.
- A quote provider selects one quote per launch. It is injected into `UniversalRemoteApp` (default `random_quote`) following the existing `probe`/`store`/`registry` dependency-injection pattern, keeping tests deterministic.
- When no quote is available (missing/empty/all-malformed file, or provider returns `None`), the menu renders without a quote row and never crashes.

## Capabilities

### New Capabilities
<!-- none -->

### Modified Capabilities
- `tui-remote`: The menu-driven entry requirement gains a companion requirement — the landing menu shows a movie/TV quote with attribution beneath the two mode buttons, chosen once per launch, and renders without it when none is available.

## Impact

- **Code**: `src/universal_remote/tui/menu.py` (render quote row), `src/universal_remote/tui/app.py` (`quote_provider` DI param + `#quote` CSS), new `src/universal_remote/tui/quotes.py` (`Quote` dataclass, `load_quotes`, `random_quote`), new data file `src/universal_remote/tui/data/quotes.txt` (~100 curated quotes).
- **Tests**: `tests/test_tui_menu.py` (quote shown / absent), new `tests/test_tui_quotes.py` (parsing, malformed/blank skipped, random selection).
- **Dependencies**: none — `random` and `importlib.resources` are stdlib.
- **Packaging**: `quotes.txt` must ship as package data (verify build config includes it).
