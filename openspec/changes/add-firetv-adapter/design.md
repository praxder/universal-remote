## Context

The remote is built on a brand-agnostic seam: a generic `Key` vocabulary, a `Capabilities` declaration, an `Adapter` protocol (`platform`, `display_name`, `capabilities()`, `pair()`, `connect()`), a `BaseSession` that gates sends against declared capabilities, and an `AdapterRegistry` that maps a device's `platform` string to an adapter. Samsung, LG, Apple TV, and Roku are the four reference adapters. Samsung/LG pair via a TV popup and return a token; Apple TV pairs via a PIN typed back through the `Prompt` hook; Roku needs no pairing at all. Each stores at most one opaque credential string in `device.credential`.

Fire TV fits this seam more cleanly than any prior adapter, because ADB pairing is popup-shaped like Samsung/LG:

- **Fire OS is an Android fork; ADB over TCP is the only viable control path.** Fire OS does not expose the Google Android TV Remote v2 service (the PIN-paired protocol used by Chromecast/Shield/Sony), and there is no companion or DIAL channel that sends key events. Control is `adb shell input keyevent <code>` for buttons and `adb shell input text <string>` for text, over a TCP ADB connection to `<ip>:5555`.
- **ADB authorization is a TV popup that yields a persisted credential.** On first connect the Fire TV shows an "Allow ADB debugging?" dialog with the host key's fingerprint. The credential is a **client-generated RSA keypair**: the app generates it, connects (triggering the dialog), and once the user accepts, the device whitelists that public key. Persisting the **private key** and replaying it on later connects skips the dialog. This is popup pairing that returns a credential — the same UI shape as Samsung/LG, so `PairingScreen` and `remote_flow.py` are untouched.

## Goals / Non-Goals

**Goals:**
- Implement the Fire TV platform against the existing `Adapter`/`Session` seam, mirroring the Samsung/LG/Apple TV/Roku structure and testing approach (injected transport, in-memory fake, no real hardware).
- Reuse the existing popup-pairing flow with zero changes to the seam, model, UI, or registry.

**Non-Goals:**
- No changes to the generic key vocabulary, `Capabilities`, `Session` seam, registry, `Device` model, or the device store's file format.
- No device discovery, info-probe prefill (Fire TV uses manual IP entry like LG/Apple TV/Roku), app-launch, now-playing, or media features beyond the generic key set.
- No channel up/down (a Fire TV streamer has no tuner; those keys are omitted so the on-screen remote disables them).
- No `identifier` use (ADB connects directly to the stored IP; there is no scan or identity to verify, like Roku).

## Decisions

### Decision: Use `adb-shell` directly over ADB
`adb-shell` (Home Assistant's async ADB client, the transport its higher-level `androidtv` library is built on) is the minimal maintained library that provides exactly what this adapter needs: an async TCP ADB device (`AdbDeviceTcpAsync`), RSA keypair generation and signing (`keygen`, `PythonRSASigner`), a `connect()` that performs the auth handshake, and `shell()` to run `input keyevent`/`input text`. The higher-level `androidtv` package adds app/state detection this adapter does not use, so wrapping `adb-shell` directly is the YAGNI fit. It is a mid-level maintained library, not raw sockets, so this is not the "raw aiohttp" path the Roku change rejected — it is the correct-altitude equivalent of `rokuecp`/`pyatv` for this platform. Every `adb-shell` call is isolated inside `adapters/firetv.py` behind injected factories; tests use a fake.

### Decision: Popup pairing that persists an RSA private-key PEM
Fire TV keeps `requires_pairing = True` (the default) and pairs through the **existing** `PairingScreen` popup path:
- `pair()` generates a fresh RSA keypair (via `adb-shell`'s `keygen`/`PythonRSASigner`), opens an `AdbDeviceTcpAsync` to `<ip>:5555`, and calls `connect(rsa_keys=[signer], auth_timeout_s=...)`. The connect blocks on the TV's authorization dialog; on accept it returns, and `pair()` returns the **private key PEM** as the credential string. The `prompt` hook is unused (popup style, like Samsung/LG), so the screen's existing default guidance ("Accept the authorization popup on your TV.") already fits.
- `connect()` rebuilds a `PythonRSASigner` from `device.credential` (the stored PEM), opens `AdbDeviceTcpAsync` to `<ip>:5555`, and `connect(rsa_keys=[signer])`. Because the public key is already whitelisted, no dialog appears.
- The signer is always built from the **in-memory per-device PEM**, never the default `~/.android/adbkey` on disk, so each saved device carries its own credential and persistence is honest.

This overloads nothing and adds nothing: the PEM is a single opaque string, exactly what `device.credential` already holds for Samsung/LG/Apple TV. No model field, no flow branch, no UI change.

### Decision: Capability set — full generic vocabulary minus channel up/down
ADB key events cover the whole generic vocabulary. Fire TV declares: the directional keys (`DPAD_UP/DOWN/LEFT/RIGHT`), OK (`DPAD_CENTER`), BACK, HOME, MENU, volume up/down, MUTE (`VOLUME_MUTE`), discrete PLAY (`MEDIA_PLAY`), PAUSE (`MEDIA_PAUSE`), the combined PLAY_PAUSE (`MEDIA_PLAY_PAUSE`), REWIND (`MEDIA_REWIND`), FAST_FORWARD (`MEDIA_FAST_FORWARD`), STOP (`MEDIA_STOP`), the number pad `NUM_0`–`NUM_9` (`KEYCODE_0`–`KEYCODE_9`), and text. It does **not** declare channel up/down: a Fire TV streamer has no tuner, so those key events would be dead. The on-screen remote already disables any key the active adapter does not declare, so channel up/down render disabled with no UI change — this is the richest capability set of any adapter (it enables buttons Samsung already declares; it adds none). Text is declared `text=True` and attempted best-effort via `input text`, reporting `TextUnsupportedError` on failure rather than silently dropping input.

### Decision: Connect verifies reachability via the ADB handshake; no identity check
ADB `connect()` to `<ip>:5555` performs a TCP connect and auth handshake, so a successful connect is itself the reachability check. `connect()` raises `ConnectionFailedError` on any failure (unreachable, refused, timeout, auth rejected) — matching Samsung/LG/Roku. Like Roku there is no identifier to verify: the user supplied the IP directly and ADB carries no device identity the seam persists.

### Decision: Fast `sendevent` key path with an `input keyevent` fallback
Hardware measurement showed `adb shell input keyevent` costs ~1.2s/key on Fire TV — the `input` binary cold-starts an ART VM every invocation, so it lags ~6× behind the WebSocket/ECP/Companion adapters (~200ms). Two faster paths were tested against the device with objective readback (wakefulness, focus via `uiautomator dump`, resumed-activity): `cmd input keyevent` returns in ~50ms but **does not inject** (a silent no-op — rejected), while `sendevent` to the remote's `/dev/input` node injects correctly at ~290ms and reaches the focused window like the physical remote.

The adapter therefore dispatches most keys via `sendevent`:
- At connect it discovers the remote input node once (`getevent -lp`, the first node advertising the d-pad keys) and fixes routing for the session. Per-key `sendevent` to an undeclared code can silently no-op, so routing is decided at connect, never per keypress.
- `EVDEV_KEYS` maps the generic keys the node supports — d-pad, OK (`DPAD_CENTER`), back, volume, mute, and the number pad — to Linux evdev scancodes (from Fire OS's `Generic.kl`). These dispatch as `sendevent <node> …` at ~290ms.
- Keys the remote node has no evdev entry for — **home** (`Generic.kl` maps only `MOVE_HOME`, not the home button), **menu**, and the media-transport keys — fall back to `input keyevent` at ~1.2s.
- If no suitable node is found or `sendevent` is unavailable, the whole session falls back to `input keyevent`, i.e. today's working behaviour.

This is a best-effort latency optimisation layered over the unchanged `input keyevent` path; it changes no observable contract (each key still sends the same action) and degrades safely on a device that does not fit. Correctness of each fast key was verified on hardware, not just that a command was emitted.

## Risks / Trade-offs

- **`adb-shell` API shape is unverified from planning.** → Confirm the entry points against the pinned version in task 1.2 (mirroring how the Roku change confirmed `rokuecp`): `keygen`/`PythonRSASigner`, `AdbDeviceTcpAsync(host, port)`, the `connect(rsa_keys=..., auth_timeout_s=...)` signature, `shell(cmd)`, `close()`, the exact ADB key-event codes, and the error types raised on failure. Every call is isolated behind an injected factory; tests use a fake.
- **Setup friction is the heaviest of any platform, but intrinsic.** → Fire TV requires the user to enable Developer Options → ADB debugging before pairing. This is not a shortcut the adapter chose; it is the only control path Fire OS exposes. Documented plainly in the README.
- **Pair-once relies on "Always allow from this computer."** → The stored-credential/no-repeat-dialog model works only if the user ticks "Always allow from this computer" in the ADB dialog. Without it the dialog reappears each connect. Only hardware-verifiable; accepted best-effort and noted in the README, in the same register as the other adapters' key-name caveats.
- **Best-effort correctness is only hardware-verifiable.** → Tests prove the adapter emits the intended `input keyevent`/`input text` shell command, not that a real Fire TV accepts it. Key-code correctness and text support are accepted best-effort, matching the other adapters and the README's existing caveats.

## Open Questions (resolve during implementation)

- **Exact `adb-shell` entry points for the installed version** (task 1.2): the async TCP device class and constructor (`AdbDeviceTcpAsync(host, port)`), keypair generation and signer construction (`keygen`, `PythonRSASigner`), the `connect(rsa_keys=..., auth_timeout_s=...)` signature and what a fresh-pair vs replay connect returns, the `shell(cmd)` and `close()` methods, and the error/timeout types. Confirm against the pinned version before finalising the key-event map and pairing logic.
- **Whether `pair()` must persist the whole PEM or a serialisable signer form.** → Persist the PEM private key text (a plain `str`), rebuilding the signer on connect; confirm the `adb-shell` keygen output is directly loadable back into a `PythonRSASigner`.

## Verification Limits

Tests use an in-memory fake `adb-shell` double, so they prove the adapter *emits the ADB action it was handed* (`input keyevent <code>` / `input text <str>`), *generates and returns a credential on pair*, and *replays the stored credential and checks reachability on connect* — not that a real Fire TV accepts it. Three things are only verifiable on hardware and accepted as best-effort:

- **Key-code correctness** — the mapped Android key-event codes (`23` for OK, `85` for play/pause, …) must match Fire OS; a wrong code passes every test and fails silently on the device.
- **Text entry** — `input text` depends on a focused on-screen field and correct escaping; declared `text=True` but reported unsupported on failure.
- **Dialog-free replay** — depends on the user having ticked "Always allow from this computer" during pairing.
