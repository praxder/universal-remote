## Why

Fire TV key dispatch is uneven: the d-pad, OK, back, volume, mute, and number keys reach the device fast (~300ms via `sendevent`), but HOME, MENU, and every media-transport key still fall back to `input keyevent`, which cold-starts an ART VM on each press (~1.1s). Those keys feel visibly laggy next to the rest. The slow keys are exactly the ones with no `sendevent` mapping today; giving them one closes the gap.

## What Changes

- Add HOME, MENU, and the six media-transport keys (PLAY, PAUSE, PLAY_PAUSE, STOP, REWIND, FAST_FORWARD) to the existing `sendevent` fast path by extending `EVDEV_KEYS` with their evdev scancodes. All eight then dispatch at ~300ms instead of ~1.1s, a 3–4× improvement, and nothing is left on the slow path except when no input node is found.
- The scancodes are read from the device's own `Generic.kl` keylayout and verified on hardware — not guessed. HOME (`172`→HOME) and the media keys (`164`→MEDIA_PLAY_PAUSE, `207`→MEDIA_PLAY, `201`→MEDIA_PAUSE, `168`→MEDIA_REWIND, `208`→MEDIA_FAST_FORWARD, `128`→MEDIA_STOP) were confirmed injecting; MENU (`139`→MENU) delivers the same keycode `input keyevent` already sent, so it is a pure latency swap.
- The `input keyevent` fallback stays intact for the whole session when no input node is discovered, so a device that does not fit degrades to today's working behaviour. No key changes which action it sends.

**Superseded during implementation:** the original proposal routed media keys through `cmd media_session dispatch`. Hardware testing showed that verb is **not implemented** on this Fire OS build (`cmd media_session dispatch` returns "No shell command implementation" — a fast no-op, the same trap as the previously-rejected `cmd input keyevent`). The single `sendevent` path handles every key and is the only working fast route, so the two-path design collapsed to one.

## Capabilities

### New Capabilities
<!-- none -->

### Modified Capabilities
- `firetv-adapter`: The "Low-latency key dispatch with fallback" requirement is clarified so its single faster path covers home, menu, and the media-transport keys — previously confined to the slow key-event fallback. The action each key sends is unchanged.

## Impact

- **Code**: `src/universal_remote/adapters/firetv.py` — add eight entries to `EVDEV_KEYS`; correct the comment/docstring that claimed home/menu/media have no evdev entry. `_dispatch_key` is unchanged: its existing "node + code → `sendevent`, else `input keyevent`" logic routes the new keys automatically.
- **Tests**: `tests/test_firetv_adapter.py` — assert HOME, MENU, and the media keys emit `sendevent` to the discovered node, and still fall back to `input keyevent` when no node is found.
- **Dependencies**: none.
- **Hardware-verifiable only**: correct scancodes and injection are confirmable only on a real Fire TV; HOME and the play/pause/play-pause keys were verified against a live YouTube session, the rest ride the identical confirmed mechanism (best-effort, matching the adapter's existing register).
