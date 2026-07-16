## Context

The Fire TV adapter (`adapters/firetv.py`) dispatches keys over ADB. It already layers a fast `sendevent` path over the slow `input keyevent` path: at connect it discovers the remote's `/dev/input` node (`find_key_node`) and, per key, sends `sendevent` when the key is in `EVDEV_KEYS`, otherwise `input keyevent FIRETV_KEYS[key]`. Measured on hardware, `sendevent` is ~290ms and `input keyevent` is ~1.2s (per-invocation ART VM cold-start).

Today `EVDEV_KEYS` covers only the directional keys, OK, back, volume, mute, and the number pad. HOME, MENU, and the six media-transport keys (PLAY, PAUSE, PLAY_PAUSE, STOP, REWIND, FAST_FORWARD) have no evdev entry and take the ~1.2s path — these are the keys the user perceives as slow. Amazon's own remote app is uniformly instant because it holds one persistent connection over the proprietary Whisperplay/`_amzn-wplay` protocol; matching that exactly is out of scope (see Non-Goals).

The prior change's design recorded home as unreachable via `sendevent` because "Generic.kl maps only MOVE_HOME, not the home button." That is the signature of testing `KEY_HOME` (Linux 102 → Android `MOVE_HOME`, a text-cursor move) instead of the physical home button's `KEY_HOMEPAGE` (Linux 172 → `KEYCODE_HOME`). This design resolves the codes empirically rather than by recall.

## Goals / Non-Goals

**Goals:**
- Move HOME and MENU off `input keyevent` onto the existing `sendevent` fast path, using scancodes captured live from the physical remote.
- Move the six media-transport keys off `input keyevent` onto a native `cmd media_session dispatch` path (~50ms, no VM).
- Keep the `input keyevent` fallback intact for any key whose fast path is unconfirmed or unavailable, so a non-fitting device degrades to today's working behaviour.
- Change no observable contract: each key sends the same action it does now.

**Non-Goals:**
- No persistent/interactive ADB shell to cut the ~290ms `sendevent` floor. `adb-shell` 0.4.4 exposes only one-shot `shell()`/`streaming_shell()`/`exec_out` — no stdin-writable interactive stream — so this needs private-API hacking for a floor the user already calls "fast." Deferred.
- No reverse-engineering of Amazon's Whisperplay remote protocol (TLS + pairing, no maintained library; the repo rejected raw-protocol paths for Roku). Deferred.
- No new keys, capabilities, pairing, or dependency changes.

## Decisions

### Decision: Capture HOME/MENU evdev codes live, do not guess
Task 1 is to run `getevent` (live stream, not `getevent -lp`) and press HOME and MENU on the physical remote, recording the `<node> <type> <code> <value>` lines each emits. Whatever node+code the device actually emits becomes the replay mapping added to `EVDEV_KEYS`. This replays a combination observed to work, which sidesteps the adapter's own documented risk that a `sendevent` to an undeclared code silently no-ops. `KEY_HOMEPAGE` (172) and `KEY_MENU` (139) are the likely answers, but the capture is the authority — if a button emits nothing on `getevent`, it has no evdev path and stays on the fallback.

*Alternative rejected:* hard-code 172/139 from recall. The prior change shipped a wrong home conclusion exactly this way; capture is cheap insurance.

### Decision: Media-transport keys via `cmd media_session dispatch`
Route PLAY→`play`, PAUSE→`pause`, PLAY_PAUSE→`play-pause`, STOP→`stop`, REWIND→`rewind`, FAST_FORWARD→`fast-forward` through `cmd media_session dispatch <verb>`. `cmd` is a native binder client into the already-running `system_server`; it does not cold-start an ART VM, so it lands near ~50ms.

This is a *different service path* from the previously rejected `cmd input keyevent`: that no-op'd because its InputManager route was blocked, whereas `media_session dispatch` reaches MediaSessionManager, which is the same session key events target. It routes to the *active* media session and no-ops when nothing is playing — but `input keyevent` media keys carry the identical constraint, so there is no behavioural regression. Correctness (that it injects) is hardware-verifiable, like the existing `sendevent` path.

*Alternative rejected:* map the media keys to `sendevent` codes. The remote's input node may not carry transport keys at all, and `media_session dispatch` is both faster and semantically exact for transport.

### Decision: Three-tier dispatch order in `_dispatch_key`
Resolve each key in order: (1) media-session table → `cmd media_session dispatch`; (2) `EVDEV_KEYS` + a discovered node → `sendevent`; (3) fall back to `input keyevent FIRETV_KEYS[key]`. Media is checked first because a transport key has no evdev entry anyway, and the ordering keeps the fallback as the single last tier — preserving the "degrades to today's behaviour" guarantee when no node is found or a key is unmapped.

## Risks / Trade-offs

- **Captured codes are device/remote-specific.** → The capture is done on the target hardware and replayed; if a different remote model emits different codes, that key falls back to `input keyevent` (still works, just slow). Same best-effort register as the existing key map.
- **`cmd media_session dispatch` may no-op with no active session.** → Matches the existing `input keyevent` media behaviour exactly; no regression, and documented as best-effort.
- **`cmd` verb names could differ across Fire OS versions.** → Verified on hardware in the same pass as the codes; on failure the key can be left on the `input keyevent` fallback with no contract change.
- **Only hardware-verifiable.** → Tests prove the adapter emits the intended `cmd media_session dispatch <verb>` / `sendevent <node> …` command, not that the device injects it — matching the adapter's existing Verification Limits.

## Open Questions

- Exact evdev node + scancodes HOME and MENU emit on the target remote (resolved by the task-1 capture).
- Whether every listed `cmd media_session dispatch` verb is accepted by the installed Fire OS build (confirmed in the same hardware pass; unaccepted verbs stay on the fallback).
