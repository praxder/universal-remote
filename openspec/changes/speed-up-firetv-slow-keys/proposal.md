## Why

Fire TV key dispatch is uneven: the d-pad, OK, back, volume, mute, and number keys reach the device fast (~290ms via `sendevent`), but HOME, MENU, and every media-transport key still fall back to `input keyevent`, which cold-starts an ART VM on each press (~1.2s). Those keys feel visibly laggy next to the rest — and next to Amazon's own remote app, which is uniformly instant. The slow keys are exactly the ones with no `sendevent` mapping today; giving them a fast device path closes the gap without changing what any key does.

## What Changes

- Dispatch the media-transport keys — PLAY, PAUSE, PLAY_PAUSE, STOP, REWIND, FAST_FORWARD — via `cmd media_session dispatch <verb>` (a native binder call into MediaSessionManager, no ART VM) instead of `input keyevent`. This is a different service path from the previously rejected `cmd input keyevent` (which silently no-ops); it targets the active media session, matching the existing constraint that `input keyevent` media keys also only act on a live session.
- Add HOME and MENU to the `sendevent` fast path, using evdev scancodes **captured live from the physical remote via `getevent`** — not guessed. Prior work concluded home was unreachable via `sendevent`; that likely tested `KEY_HOME` (102 → `MOVE_HOME`, a cursor move) rather than the home button's `KEY_HOMEPAGE` (172 → `KEYCODE_HOME`). The capture resolves this empirically.
- Preserve the existing `input keyevent` fallback for any key whose fast path is unavailable or whose code the capture does not confirm, so a device that does not fit degrades to today's working behaviour.

## Capabilities

### New Capabilities
<!-- none -->

### Modified Capabilities
- `firetv-adapter`: The "Low-latency key dispatch with fallback" requirement is broadened to cover two fast device paths (an evdev `sendevent` path and a media-session dispatch path for transport keys) rather than a single one, so home, menu, and the media-transport keys are no longer confined to the slow key-event fallback. The action each key sends is unchanged.

## Impact

- **Code**: `src/universal_remote/adapters/firetv.py` — extend `EVDEV_KEYS` with captured HOME/MENU scancodes; add a media-session dispatch table and route those keys through it in `FireTvSession._dispatch_key`; the `input keyevent` fallback stays as the final tier.
- **Tests**: `tests/test_firetv_adapter.py` — assert media keys emit the `cmd media_session dispatch` command and that HOME/MENU emit `sendevent` to the discovered node; fallback behaviour unchanged.
- **Dependencies**: none (uses existing `adb-shell` `shell()` path).
- **Hardware-verifiable only**: correct scancodes and that `cmd media_session dispatch` injects are confirmable only on a real Fire TV, matching the adapter's existing best-effort register.
