## 1. Capture device facts (hardware — DONE during investigation)

- [x] 1.1 Discovered the remote input node is `/dev/input/event4` ("amzkeyboard"), the node `find_key_node` already picks. It advertises `KEY_HOMEPAGE`, `KEY_MENU`, and all media-transport keys.
- [x] 1.2 Read scancodes from the device's `Generic.kl` (the node has no device-specific `.kl`): HOME=172, MENU=139, PLAY_PAUSE=164, PLAY=207, PAUSE=201, STOP=128, REWIND=168, FAST_FORWARD=208.
- [x] 1.3 Verified injection on hardware: `sendevent 172` moved focus to the launcher (HOME); against a live YouTube session `sendevent 164` toggled play/pause, `201` paused, `207` resumed. `cmd media_session dispatch` was found **unimplemented** ("No shell command implementation") — abandoned in favour of `sendevent`.
- [x] 1.4 Recorded confirmed codes and the `media_session` finding in `design.md`.

## 2. Extend the fast path

- [x] 2.1 Write failing tests: sending HOME, MENU, and each media key (PLAY, PAUSE, PLAY_PAUSE, STOP, REWIND, FAST_FORWARD) over a session with a discovered key node emits `sendevent <node> …` with the mapped scancode (not `input keyevent`), using the in-memory fake device. (Parametrized test; confirmed red — 8 KeyErrors.)
- [x] 2.2 With no discovered node, HOME/MENU/media keys still fall back to `input keyevent`. (Covered by the existing no-node fallback test and the auto-adapting all-keys test.)
- [x] 2.3 Add the eight confirmed scancodes to `EVDEV_KEYS`.
- [x] 2.4 Run the new tests to green (`_dispatch_key` unchanged — its node+code branch routes them). 37/37 in the file pass.

## 3. Correct docs + regression + preflight

- [x] 3.1 Fixed the `EVDEV_KEYS` comment and `FireTvSession` docstring that claimed home/menu/media have no evdev entry; now state the fallback is reached only when no node is discovered.
- [x] 3.2 Updated the README's "Key latency" caveat: every key uses the fast path; fallback only when no node is found.
- [x] 3.3 Existing fast keys and the no-node fallback still behave as before (all-keys and no-node tests pass).
- [x] 3.4 Preflight: `ruff format` clean, `ruff check` clean, full suite 252 passed.
- [x] 3.5 Hardware smoke test in the app (user): confirmed HOME, MENU, and media keys trigger quickly on the real device, and the app reconnects after the earlier contention incident.
