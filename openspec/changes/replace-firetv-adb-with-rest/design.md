## Context

The Fire TV adapter drives the device through `adb-shell` over TCP port 5555. That requires Developer options and ADB debugging to stay enabled, and the adapter's connection contends with any other ADB use of the same device.

Fire OS exposes the undocumented REST API used by Amazon's own Fire TV remote app. Every fact below was verified against a Fire TV Stick 4K (model AFTMM, Fire OS 6.7.1.1) with ADB debugging switched **off** and port 5555 confirmed closed.

```
① POST http://<ip>:8009/apps/FireTVRemote      DIAL wake → 201; opens :8080 in ~1.5s
② POST https://<ip>:8080/v1/FireTV/pin/display  → PIN shown on the television
③ POST https://<ip>:8080/v1/FireTV/pin/verify   {"pin":"…"} → {"description":"<token>"}
④ POST https://<ip>:8080/v1/FireTV?action=home  + X-Client-Token
```

Constants: `X-Api-Key: 0987654321` (a fixed value in the protocol, not a per-user secret), `User-Agent: okhttp/4.10.0`. TLS is self-signed, so certificate verification must be disabled for this host. The token is short (7 characters) and survives a re-wake.

Measured routes:

| Route | POST | GET |
|---|---|---|
| `/v1/FireTV?action=` | navigation keys | `{"isVolumeControlsSupported":false}` |
| `/v1/FireTV/keyboard` | set focused field contents | `{"state":"text"\|"hidden","text":"…"}` |
| `/v1/media?action=` | `play`, `pause` | — |
| `/v1/FireTV/app/{package}` | launch app | — |
| `/v1/FireTV/status` | — | OS version |
| `/v1/FireTV/apps` | — | installed apps |
| `/v1/FireTV/text` | exists but rejects every input — a decoy | — |

Measured nav latency: 62–70ms warm, versus roughly 250ms per key for the ADB `sendevent` path, which spawns four processes per press.

## Goals / Non-Goals

**Goals:**

- Remove every ADB dependency from the Fire TV path so developer mode can stay off and other ADB work is unimpeded.
- Keep the adapter seam unchanged: `pair`, `connect`, and a `Session` that sends keys and text.
- Report failures truthfully rather than inferring success from a status code that does not mean success.

**Non-Goals:**

- Exposing the newly available state queries (installed apps, OS version, app launch) as product features. They are useful and reachable, but nothing in the current UI consumes them.
- Supporting press-and-hold. The API supports it and ADB did not, but no caller requests a held key today; adding it is a separate change.
- Preserving existing Fire TV pairings. The credential format changes and re-pairing is required.
- Retaining an ADB fallback for the keys the REST API cannot send.

## Decisions

### Replace ADB entirely rather than adding REST alongside it

A hybrid — REST for most keys, ADB for the rest — would keep an ADB connection open and reintroduce exactly the conflict this change exists to remove, in exchange for two keys (`PLAY_PAUSE`, `STOP`). Rejected.

The alternative of keeping ADB as an opt-in transport was also rejected: it doubles the adapter's surface and its test matrix to serve a case the user has explicitly said they do not want.

### Send discrete keys with an empty request body

The device accepts three body forms, and they differ in what they report, not in what they do:

| Body | Status | Key dispatched? |
|---|---|---|
| *(empty)* | `200` | yes |
| `{"keyActionType":"keyDown"}` / `keyUp` | `200` | yes |
| `{"keyActionType":"keyDownUp"}` | `500 NullPointerException` | **yes** |
| any other JSON | `500 NullPointerException` | presumed yes |

The 500 is raised while building the response, after dispatch — confirmed visually, with three presses returning 500 and moving focus three tiles. So a JSON body works but makes every response a 500, valid action or not, which destroys error reporting.

With an empty body the device returns `200` for a valid action and `400` for an unknown one. That distinction is what the "Key dispatch over the remote HTTP API" requirement depends on, so the empty-body form is the one to use. Press-and-hold, if it is ever wanted, uses the split `keyDown`/`keyUp` form, which also returns clean 200s; the combined `keyDownUp` should never be sent.

### Map FAST_FORWARD and REWIND onto the player-context d-pad

The API has no transport action for either — `fast_forward`, `rewind`, `scan` (with and without a direction), `next`, `previous`, and `seek` all return 400, re-verified during live playback so this is not an idle-session artifact. During playback, `dpad_right` skips forward 10 seconds per press (three presses measured at +30s) and `dpad_left` skips back.

This is a Fire TV **player-UI convention**, not a protocol guarantee, and it was confirmed in YouTube only. An app with a custom player may treat the d-pad differently. The alternative is dropping both keys; mapping them is better than losing them, but the assumption should be revisited if a player is found where it fails.

### Route the number pad through the keyboard endpoint

No arbitrary-keycode path exists. Digits therefore go through `/v1/FireTV/keyboard`, which means they only work when a text field is focused — ADB's `input keyevent` worked anywhere. On a tuner-less streamer digits are used almost exclusively inside text fields, so the loss is small.

Because the endpoint **replaces** the field's contents rather than appending (no append mode exists: `toAppend`, `append: true`, `mode: "append"`, `replace: false`, and `?action=append` are all ignored or rejected), sending a digit must read the current contents via `GET /v1/FireTV/keyboard` and write back the concatenation.

### Use `/v1/FireTV/keyboard` for text, and check `state` before reporting success

`/v1/FireTV/text` exists as a route but rejects every input shape tried — roughly twenty field names across JSON body, query string, and `text/plain`, retested with a field focused and the on-screen keyboard up, with a `backspace` control returning 200 in the same run. It is a decoy. The working endpoint is `/v1/FireTV/keyboard`.

Verified by reading the value back: it replaces field contents, `{"text":""}` clears, and spaces, punctuation, and Unicode including emoji round-trip byte-exact (`café ☕`), as does a 113-character string. This is strictly better than the ADB path, whose entire reason for `adapters/adb_text.py` was escaping spaces and `%` for `input text`, which cannot send Unicode at all.

`GET /v1/FireTV/keyboard` reports `{"state":"hidden"}` when nothing is focused, and a POST in that state returns a hollow `200` while doing nothing. Text sends must therefore check `state` first and report text-unsupported when it is `hidden`.

### Drop the volume keys

`GET /v1/FireTV` reports `isVolumeControlsSupported: false`, and three `volume_up` calls returning `200` produced no audible change. The flag is truthful and the 200s are hollow.

This is likely not a regression: a stick outputs over HDMI and its physical remote drives volume over CEC/IR rather than through Fire OS key events, so the ADB path probably never worked either. That was not re-tested, since doing so requires re-enabling ADB. Either way, declaring keys that demonstrably do nothing is worse than omitting them.

### Keep declared capabilities static

`GET /v1/FireTV` and `/v1/FireTV/status` make per-device capability probing cheap and truthful, and there is a real device split — this AFTMM rejects `keyDownUp` while newer models accept it. Probing was still rejected: it adds connect-time cost and makes capabilities non-static for a split observed on exactly one device, against a codebase where every other adapter declares capabilities statically. The probe endpoints are documented here so a future change can revisit this cheaply.

### Change the reachability port to 8009

Port 5555 is closed on a stock device, so leaving it would mark every Fire TV unreachable. Port 8080 is wrong too — it is closed until the DIAL wake runs, so an idle device would read unreachable. Port 8009 was observed open before any wake and stays open, and probing it is a plain TCP connect with no side effect, which is what `device-reachability` requires.

### Discovery is unchanged

`_amzn-wplay._tcp.local.` with the friendly name in the TXT `n` key already works and is independent of the transport.

## Risks / Trade-offs

- **The API is undocumented and could change in a Fire OS update** → It is the transport Amazon's own remote app depends on, so it is unlikely to vanish silently. Behaviour is pinned by the spec's scenarios, so a break surfaces as failing tests rather than silent misbehaviour.

- **Findings are verified on one device and one Fire OS version** → The `keyDownUp` NPE is already known to be version-dependent. The chosen dispatch form (empty body) avoids that path entirely, so it should be the most portable of the three. `GET /v1/FireTV/status` exposes the OS version if version-specific handling ever becomes necessary.

- **The FF/REW d-pad mapping rests on a player-UI convention** → Confirmed in YouTube only; a custom player may not scrub on d-pad. Documented above as an assumption to revisit.

- **Users must re-pair every Fire TV** → Unavoidable; the credential format changes. Pairing is a short flow and the failure mode is a clear pairing error, not silent breakage.

- **TLS certificate verification must be disabled** → The device presents a self-signed certificate. This is a plaintext-equivalent trust model on the local network, the same posture the ADB path had, and it must be scoped to the Fire TV host rather than applied process-wide.

- **`X-Api-Key` is a hardcoded protocol constant** → It is not a user secret and carries no entitlement on its own; the `X-Client-Token` from pairing is what authorises commands. Requests without that token are rejected with `403`, verified.

- **The idle remote service may stop** → Each command is a standalone request against a service that can go away. The session should re-wake and retry once on a connection failure rather than surfacing a transient error.

## Migration Plan

1. Rewrite `adapters/firetv.py` against the REST API behind an injected HTTP seam, mirroring how the current adapter injects its device factory.
2. Rewrite `tests/test_firetv_adapter.py` against that seam.
3. Delete `adapters/adb_text.py` and `tests/test_adb_text.py`, whose only non-test users are `firetv.py:24` and `firetv.py:171`.
4. Drop the `adb-shell` dependency from `pyproject.toml` once no adapter imports it.
5. On first run after upgrade, a saved Fire TV fails to connect because its stored ADB key is not a valid token; the user re-pairs through the existing flow.

Rollback is a revert: the change is confined to the Fire TV adapter, its tests, the deleted text helper, and one dependency.

## Open Questions

- Should the session re-wake proactively on an idle timer, or only reactively after a failed request? Reactive is simpler and is the default assumed above; the upstream reference re-wakes after five minutes idle.
- Are `power` and `sleep` worth exposing? Both exist in the API and were deliberately not tested against the user's television. Neither is in the current generic key set, so this is out of scope until a key is defined for it.
