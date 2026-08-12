## Why

The on-screen remote today exposes only ten keys — the D-pad, OK, Back, Home, volume, and mute. Real remotes do more: a menu button, channel up/down, a number pad, and media transport (play, pause, stop, rewind, fast-forward). Each adapter's protocol already accepts more codes than the UI surfaces, so the buttons exist in the platform but not in the app. The seam already disables any key an adapter does not declare, so the missing piece is vocabulary and buttons — not new gating.

## What Changes

- The generic key vocabulary gains: `MENU`, `CH_UP`, `CH_DOWN`, `PLAY`, `PAUSE`, `PLAY_PAUSE`, `REWIND`, `FAST_FORWARD`, `STOP`, and `NUM_0`–`NUM_9` (nineteen new keys).
- Each adapter maps only the new keys its protocol supports; unmapped keys stay disabled by the existing capability machinery. Notably:
  - **Apple TV** gains channel up/down, all three of play/pause/play-pause, skip-as-rewind/fast-forward, and stop. It does **not** gain `MENU` (its menu button already backs the `BACK` key) or the number pad (pyatv exposes no digits) — those buttons render disabled.
  - **LG** and **Samsung** gain menu, channel, the full number pad, separate play/pause, rewind/fast-forward, and stop. Neither has a combined `PLAY_PAUSE`, so that button renders disabled on both.
- The remote surface renders the new buttons, grouped as a top row (menu/home/back), the D-pad, a channel + volume row, a media-transport row, and a 3×4 number pad. Every button is mouse-clickable.
- **Rule:** a button is enabled if and only if the active adapter's protocol supports its key — "supported" means the protocol accepts the code, not that a physical remote carries the button.
- Layout: to fit the number pad and media row without scrolling on an 80×24 terminal, remote buttons render one row tall (compact, borderless).
- Keyboard: digit keys `0`–`9` send `NUM_0`–`NUM_9`. The other new buttons are mouse-only (no keyboard binding), matching how Mute works today.
- "Source", "Search", and "Settings" buttons are **not** added: source switching is a different mechanism (input selection, not a key) with no Apple TV or LG key, and search/settings have no clean code on most adapters.

## Capabilities

### New Capabilities

_None._

### Modified Capabilities

- `remote-control-core`: the generic key vocabulary expands to cover menu, channel up/down, play, pause, play/pause, rewind, fast-forward, stop, and the digits 0–9.
- `tui-remote`: the on-screen remote surface renders the expanded button set; keyboard control gains digit keys `0`–`9` for the number pad.

## Impact

- `src/universal_remote/keys.py` — nineteen new `Key` members.
- `src/universal_remote/adapters/appletv.py` — extend `APPLETV_RC_KEYS` with channel/media/stop (no menu, no digits).
- `src/universal_remote/adapters/lg.py` — extend `LG_BUTTONS` with menu/channel/media/stop/digits.
- `src/universal_remote/adapters/samsung.py` — extend `SAMSUNG_KEYS` with menu/channel/media/stop/digits.
- `src/universal_remote/tui/remote_screen.py` — render the new button groups; add digit-key bindings; the existing `on_mount` disable loop covers the new keys unchanged.
- `src/universal_remote/tui/app.py` (or a new remote stylesheet) — compact one-row button CSS scoped to `RemoteScreen` so the fuller remote fits without scrolling.
- `tests/test_keys.py` — the hardcoded vocabulary set expands to the new keys.
- `tests/test_tui_remote_surface.py`, `tests/test_tui_capabilities.py`, `tests/test_lg_adapter.py`, `tests/test_samsung_adapter.py`, `tests/test_appletv_adapter.py` — new-button and per-adapter mapping tests.
- No store, dependency, or pairing/connect changes.
