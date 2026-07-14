## Context

The remote is built on a brand-agnostic seam: a generic `Key` vocabulary, a `Capabilities` declaration, an `Adapter` protocol (`platform`, `display_name`, `capabilities()`, `pair()`, `connect()`), a `BaseSession` that gates sends against declared capabilities, and an `AdapterRegistry` that maps a device's `platform` string to an adapter. Samsung and LG are the two reference adapters. Both pair the same way: `pair()` opens a connection, the TV shows a popup, the user taps "Allow", and a single opaque credential (token / client-key) comes back to persist and replay. Neither uses the `Prompt` hook, and `PairingScreen` never supplies one.

Apple TV breaks that mould in two ways the seam anticipated but no adapter has exercised:

1. **Pairing returns a value only after the user reads a PIN off the TV and types it back.** `pyatv` reports `device_provides_pin == True` for Apple TV — the device shows a four-digit PIN and the app must call `pairing.pin(<entered>)` before `pairing.finish()`. This is exactly what `Adapter.pair(prompt=...)` was designed for, but `PairingScreen` (`remote_flow.py`) calls `adapter.pair(self._device)` with no prompt and hardcodes popup guidance.
2. **Connecting needs device identity plus a service, not just an IP.** `pyatv.connect(config, loop)` requires a config carrying an identifier and at least one service; it raises otherwise. Credentials are per-protocol (`{Companion: "…", AirPlay: "…"}`), not one string.

## Goals / Non-Goals

**Goals:**
- Implement the Apple TV platform against the existing `Adapter`/`Session` seam, mirroring the Samsung/LG structure and testing approach (injected transport, in-memory fake, no real hardware).
- Wire PIN entry through `PairingScreen` so Apple TV pairs end-to-end, without changing the popup-only flow for Samsung and LG.
- Add the minimum model surface (`identifier`) to reconnect, keeping the single-string credential.

**Non-Goals:**
- No multi-protocol pairing (AirPlay/MRP/RAOP) — Companion alone drives the generic remote key set.
- No changes to the generic key vocabulary, `Capabilities`, `Session` seam, registry, or the store's file format beyond one optional field.
- No network discovery UI, app-launch, now-playing, or media-transport features beyond the generic key set.
- No MUTE on Apple TV (no Companion equivalent) and no power key (Apple TV has no session power-off in the generic set used here).

## Decisions

### Decision: Use `pyatv` over the Companion protocol
`pyatv` is the de-facto async Python library for Apple TV (the basis of Home Assistant's `apple_tv` integration). The **Companion** protocol carries the remote-control surface (D-pad, select, menu, home, volume) for modern (tvOS 15+) Apple TVs and pairs with a device-shown PIN. Pairing only Companion keeps a single credential string, satisfying the "single credential + identifier" model. AirPlay would add streaming/volume nuance and a second credential for no gain to a button remote — explicitly out of scope.

### Decision: Companion-only capability set; MUTE and power dropped
Apple TV declares support for the directional keys, OK (select), BACK (menu), HOME, volume up, and volume down. It does **not** declare MUTE — `pyatv`'s remote control has no mute toggle — or POWER. The on-screen remote already disables any key the active adapter does not declare (the "capability-driven button state" requirement), so the MUTE button renders disabled for Apple TV with no UI change. Text is declared `text=True` and attempted best-effort via `pyatv`'s keyboard interface, reporting `TextUnsupportedError` on failure rather than silently dropping input — matching the seam's contract.

### Decision: PIN pairing wires the existing `Prompt` hook through `PairingScreen`
The adapter's `pair()` gains real use of the `prompt` parameter: it begins Companion pairing (`pairing.begin()`), then `await prompt(<message>)` to obtain the PIN the TV is showing, calls `pairing.pin(int(value))` and `pairing.finish()`, and returns `pairing.service.credentials`. If `prompt` is `None`, `pair()` raises `PairingCancelledError` (a PIN adapter cannot pair without a way to ask).

`PairingScreen` changes minimally:
- It passes a bound `prompt` coroutine to `adapter.pair(self._device, prompt=…)`.
- When the adapter awaits `prompt(message)`, the screen swaps its guidance for a PIN-entry state (the adapter-supplied `message`, a text `Input`, and a Submit button) and resolves the awaited coroutine with the submitted value. This bridges the pairing worker and the UI with an `asyncio.Future` the submit handler completes.
- Guidance text becomes adapter-driven: the default remains the popup line; Apple TV's prompt message ("Enter the PIN shown on your Apple TV") is shown only when the adapter asks.
- Cancellation is unchanged: Esc/Cancel cancels the worker, which cancels the awaited prompt, surfacing the existing `PairingCancelledError` → dismiss-without-storing path.

Samsung and LG never call `prompt`, so their pairing renders exactly as today.

### Decision: Persist a reconnection `identifier`; keep one credential string
`Device` gains `identifier: str | None = None`. During pairing the adapter records the `pyatv` device identifier onto the passed `Device` (it already receives it) and returns the Companion credential as the credential string — leaving `Adapter.pair() -> str` and the Samsung/LG adapters untouched. `PairingScreen` persists the device after pairing, so the identifier and credential round-trip together. The store's loader already ignores unknown keys and serialises all model fields, so old files load unchanged and the new field appears only for devices that set it.

### Decision: Connect via a fast unicast host scan, verifying identity
Companion's service **port is assigned dynamically and discovered over mDNS** — it is not a fixed constant and can change across an Apple TV reboot. A hand-built `ManualService` would therefore have to persist a volatile port that silently goes stale. Instead, `connect()` runs `pyatv.scan(loop, hosts=[device.ip])` — a **unicast probe of the one known IP**, not a full-network mDNS sweep — to obtain a fresh config, verifies the scanned identifier equals the stored `device.identifier` (guarding against a different device now sitting at that IP), applies the stored credential with `set_credentials(Protocol.Companion, device.credential)`, and connects. Any failure — not found, identity mismatch, transport error, or timeout — surfaces as `ConnectionFailedError`, matching Samsung/LG. This is why the `identifier` field earns its place: it is the reconnect-time identity check.

**Alternatives considered:**
- *Manual `ManualService` config, no scan* — avoids discovery latency but must persist the dynamic Companion port, which breaks after a reboot; rejected for that fragility.
- *Full-network scan by identifier each connect* — robust to IP changes but slow (multi-second mDNS sweep) and needs the whole subnet reachable; the unicast host scan is fast and sufficient because the user supplied a specific IP.

## Risks / Trade-offs

- **`pyatv` API surface differs sharply from the Samsung/LG clients** (scan/pair/connect objects, an event loop parameter, per-protocol credentials). → Isolate every `pyatv` call inside `adapters/appletv.py` behind an injected factory; tests use a fake, so the seam and TUI never depend on the library shape.
- **`PairingScreen` grows a genuinely new interaction (mid-pairing input).** → Keep the prompt bridge tiny (one `Future`, one input state) and drive it entirely from the adapter's `prompt` call, so non-PIN adapters exercise none of it and existing pairing tests stay green.
- **Companion port drift / IP reuse.** → The connect-time host scan re-resolves the port every time and the identifier check rejects a wrong device at a reused IP; a moved device (new IP) is corrected by editing the device's IP, as today.
- **Best-effort correctness is only hardware-verifiable.** → As with Samsung/LG, tests prove the adapter emits the intended `pyatv` call, not that a real Apple TV accepts it. Key-name/method correctness and text support are accepted best-effort, in the same register as the README's existing caveats.

## Open Questions (resolve during implementation)

- **Exact `pyatv` entry points for the installed version**: `scan(loop, hosts=[…])`, `pair(config, Protocol.Companion, loop)` → `begin()/device_provides_pin/pin()/finish()/has_paired/service.credentials/close()`, `connect(config, loop)`. Nav/select/menu/home/**volume** all map to `atv.remote_control` (`up/down/left/right/select/menu/home/volume_up/volume_down`); text uses the keyboard interface (`text_set`/`text_append`). Confirm against the pinned version before finalising the mapping (mirrors how the LG change confirmed `aiowebostv` 0.7.5 entry points during task 1.2).
- **Volume routing** (revised post-implementation): volume maps to `atv.remote_control.volume_up()/volume_down()`, **not** `atv.audio.*`. The original plan chose `Audio` because `RemoteControl.volume_*` is marked deprecated, but on hardware `CompanionAudio.volume_up/volume_down` fire the HID key and then block up to 5s on `asyncio.wait_for` for a volume-state acknowledgement that an idle Apple TV never sends — raising `TimeoutError` and crashing the remote. `RemoteControl.volume_*` presses the same HID key fire-and-forget, which is the correct behaviour for a button remote; its deprecation is a docstring note only (`pyatv`'s `@deprecated` emits a `DeprecationWarning`, no runtime error, and the pinned `pyatv 0.18.0` facade still routes it to the Companion implementation). Whether the key reaches the TV directly or via HDMI-CEC on the user's setup remains best-effort. `pyatv` exposes no mute on either `RemoteControl` or `Audio` (confirmed against source), so MUTE is correctly omitted from the capability set.

## Verification Limits

Tests use an in-memory fake `pyatv` double, so they prove the adapter *emits the action it was handed* and *drives the pair/connect sequence in order*, not that a real Apple TV accepts it. Two things are only verifiable on hardware and accepted as best-effort:

- **Remote-control method correctness** — the mapped `pyatv` methods (`select` for OK, `menu` for BACK, …) must match the library's vocabulary; a wrong method passes every test and fails silently on the device.
- **Text entry** — keyboard support varies by focus/app; declared `text=True` but reported unsupported on failure.
