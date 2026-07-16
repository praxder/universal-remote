## 1. Capture device facts (hardware, empirical — do first)

- [ ] 1.1 On the target Fire TV, run `adb shell getevent` (live stream) and press HOME, then MENU, on the physical remote; record the `<node> <type> <code> <value>` lines each emits. The node is expected to match the d-pad node `find_key_node` already discovers.
- [ ] 1.2 Confirm HOME/MENU by replaying the captured codes: `adb shell "sendevent <node> 1 <code> 1; sendevent <node> 0 0 0; sendevent <node> 1 <code> 0; sendevent <node> 0 0 0"` and observe the action fire on-screen.
- [ ] 1.3 Confirm each media verb injects: `adb shell cmd media_session dispatch <verb>` for `play`, `pause`, `play-pause`, `stop`, `rewind`, `fast-forward` while media is playing; note any verb the installed Fire OS rejects.
- [ ] 1.4 Record the confirmed HOME/MENU scancodes and the accepted media verbs in the design's Open Questions section (or note which stay on the fallback).

## 2. Media-session dispatch path

- [ ] 2.1 Write failing tests: sending each of PLAY, PAUSE, PLAY_PAUSE, STOP, REWIND, FAST_FORWARD over a session emits `cmd media_session dispatch <verb>` with the correct verb (using the in-memory fake device).
- [ ] 2.2 Add a `MEDIA_SESSION_KEYS: dict[Key, str]` table mapping the six transport keys to their verbs, using only verbs confirmed in 1.3.
- [ ] 2.3 In `FireTvSession._dispatch_key`, check `MEDIA_SESSION_KEYS` first and dispatch `cmd media_session dispatch <verb>` when matched.
- [ ] 2.4 Run the media tests to green.

## 3. Home/menu evdev path

- [ ] 3.1 Write failing tests: with a discovered key node, sending HOME and MENU emits `sendevent <node> …` (not `input keyevent`); with no node, both fall back to `input keyevent`.
- [ ] 3.2 Add the captured HOME/MENU scancodes (from 1.1/1.2) to `EVDEV_KEYS`.
- [ ] 3.3 Confirm `_dispatch_key`'s existing evdev branch now covers HOME/MENU with no further change (the three-tier order: media → evdev → `input keyevent`).
- [ ] 3.4 Run the home/menu tests to green.

## 4. Regression + preflight

- [ ] 4.1 Confirm existing fast keys (d-pad, OK, back, vol, mute, numbers) still emit `sendevent`, and the no-node session still falls back entirely to `input keyevent`.
- [ ] 4.2 Update the `firetv-adapter` docstring/comments in `firetv.py` to describe the three-tier dispatch (media-session → evdev → key-event) and drop the stale "home has no evdev entry" note.
- [ ] 4.3 Update the README's Fire TV section if it lists which keys are fast.
- [ ] 4.4 Preflight: format, lint, and run the full test suite; all green.
- [ ] 4.5 Hardware smoke test: confirm HOME, MENU, and the media-transport keys now trigger quickly on the real device, matching the d-pad's responsiveness.
