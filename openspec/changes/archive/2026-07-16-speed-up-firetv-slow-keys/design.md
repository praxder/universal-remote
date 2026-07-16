## Context

The Fire TV adapter (`adapters/firetv.py`) dispatches keys over ADB. It already layers a fast `sendevent` path over the slow `input keyevent` path: at connect it discovers the remote's `/dev/input` node (`find_key_node`) and, per key, sends `sendevent` when the key is in `EVDEV_KEYS`, otherwise `input keyevent FIRETV_KEYS[key]`. Measured on hardware over ADB: `sendevent` ~300ms, `input keyevent` ~1.1s (per-invocation ART VM cold-start).

Today `EVDEV_KEYS` covers only the directional keys, OK, back, volume, mute, and the number pad. HOME, MENU, and the six media-transport keys have no evdev entry and take the ~1.1s path — these are the keys the user perceives as slow.

Hardware investigation on the target device (Fire OS, node `/dev/input/event4` "amzkeyboard", the node `find_key_node` already discovers) resolved the earlier unknowns:

- The node advertises `KEY_HOMEPAGE`, `KEY_MENU`, `KEY_PLAYPAUSE`, `KEY_PLAY`, `KEY_PAUSE`(CD), `KEY_STOP`, `KEY_REWIND`, and `KEY_FASTFORWARD` — so the physical remote's keys route through this node.
- It has no device-specific `.kl`, so it uses `Generic.kl`, which maps: `172`→HOME, `139`→MENU, `164`→MEDIA_PLAY_PAUSE, `207`→MEDIA_PLAY, `201`→MEDIA_PAUSE, `128`→MEDIA_STOP, `168`→MEDIA_REWIND, `208`→MEDIA_FAST_FORWARD.
- The prior change's "Generic.kl maps only MOVE_HOME, not the home button" was simply wrong: `Generic.kl` maps `172`→HOME. The MOVE_HOME confusion is the `KEY_HOME`(102)→`MOVE_HOME` vs `KEY_HOMEPAGE`(172)→`HOME` distinction.

## Goals / Non-Goals

**Goals:**
- Move HOME, MENU, and the six media-transport keys off `input keyevent` onto the existing `sendevent` fast path, using scancodes read from the device's own `Generic.kl` and verified on hardware.
- Keep the `input keyevent` fallback intact for when no input node is discovered, so a non-fitting device degrades to today's working behaviour.
- Change no observable contract: each key sends the same action it does now.

**Non-Goals:**
- No `cmd media_session dispatch` path — see the decision below; it is unimplemented on this Fire OS build.
- No persistent/interactive ADB shell to cut the ~300ms `sendevent` floor. `adb-shell` 0.4.4 exposes only one-shot `shell()`/`streaming_shell()`/`exec_out` — no stdin-writable interactive stream. Deferred.
- No reverse-engineering of Amazon's Whisperplay remote protocol (TLS + pairing, no maintained library; the repo rejected raw-protocol paths for Roku). Deferred.
- No new keys, capabilities, pairing, or dependency changes.

## Decisions

### Decision: One fast path — `sendevent` to the discovered node — for every key
Extend `EVDEV_KEYS` with the eight scancodes above; `_dispatch_key` is unchanged and routes them via `sendevent` automatically. After this, every key `FIRETV_KEYS` declares also has an `EVDEV_KEYS` entry, so `input keyevent` is reached only when no node was discovered (the whole-session fallback). This is the minimal change — eight dict entries, no new dispatch branch, no new table.

*Confidence:* the mechanism (evdev → `Generic.kl` → dispatch on node event4) is proven end-to-end: HOME (`172`) moved the focused activity from a settings screen to the launcher, and the existing shipped d-pad set already rides this exact node/file.

*Pure latency swap:* each new fast code decodes to the same Android keycode the slow `input keyevent` path already sent, so this adds no new behavioural surface — only faster transport for an identical `KeyEvent`:

| Key | evdev (Generic.kl) | == `input keyevent` (`FIRETV_KEYS`) |
|-----|--------------------|-------------------------------------|
| HOME | 172 → HOME | 3 (KEYCODE_HOME) |
| MENU | 139 → MENU | 82 |
| PLAY | 207 → MEDIA_PLAY | 126 |
| PAUSE | 201 → MEDIA_PAUSE | 127 |
| PLAY_PAUSE | 164 → MEDIA_PLAY_PAUSE | 85 |
| STOP | 128 → MEDIA_STOP | 86 |
| REWIND | 168 → MEDIA_REWIND | 89 |
| FAST_FORWARD | 208 → MEDIA_FAST_FORWARD | 90 |

Media routing over `sendevent` was proven to reach the active session (YouTube state flips), so STOP/REWIND/FAST_FORWARD carry only the same per-app-interpretation caveat the old path already had — not a routing unknown.

### Decision: Do NOT use `cmd media_session dispatch`
The original proposal routed the media keys through `cmd media_session dispatch <verb>`, reasoning it was a native binder path distinct from the rejected `cmd input keyevent`. Hardware falsified this: on the target Fire OS build, `cmd media_session dispatch <verb>` returns **"No shell command implementation"** and injects nothing — a fast-returning no-op, the identical trap as `cmd input`. The `media_session` service exists but implements no shell `dispatch`. It is therefore unusable here, and `sendevent` (which does inject media keys — see verification) is both the working and the simpler path.

*Verification:* against a live YouTube session, `sendevent 164` flipped playback `state=3`(PLAYING)→`state=2`(PAUSED); `sendevent 201` paused; `sendevent 207` resumed from paused. So `sendevent` media keys route to the active media session — the exact behaviour `cmd media_session dispatch` was meant to provide.

### Decision: Read scancodes from the device, verify by injection
Codes were taken from the device's own `/system/usr/keylayout/Generic.kl` (authoritative for the "amzkeyboard" node) rather than recalled, then confirmed by injecting and observing effect (focused-activity readback for HOME; media-session `state` readback for play/pause). Any code that could not be confirmed injecting stays out of `EVDEV_KEYS` and falls back to `input keyevent` (slow but working) rather than shipping fast-but-unverified. STOP/REWIND/FAST_FORWARD ride the same confirmed mechanism; their per-app effect is best-effort, as the adapter's register already states.

## Risks / Trade-offs

- **Captured codes are device/remote-specific.** → Codes come from the target hardware's `Generic.kl`; a different remote/node that emits different codes would fall back to `input keyevent` (still works, just slow). Same best-effort register as the existing key map.
- **Media keys no-op with no active session.** → Identical to the existing `input keyevent` media behaviour; no regression.
- **Per-app FAST_FORWARD/REWIND/STOP behaviour varies.** → The keycode reaches the active session (confirmed delivery); how an app interprets it is app-specific and best-effort.
- **Only hardware-verifiable.** → Tests prove the adapter emits `sendevent <node> …` for these keys, not that the device injects — matching the adapter's existing Verification Limits. Core keys were verified on real hardware.

## Open Questions

- None outstanding. The evdev node, the eight scancodes, and the death of `cmd media_session dispatch` were all resolved on hardware during investigation.
