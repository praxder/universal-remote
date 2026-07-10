## Context

The remote is built on a brand-agnostic seam: a generic `Key` vocabulary, a `Capabilities` declaration, an `Adapter` protocol (`platform`, `capabilities()`, `pair()`, `connect()`), a `BaseSession` that gates sends against declared capabilities, and an `AdapterRegistry` that maps a device's `platform` string to an adapter. Today only the Samsung Tizen adapter is registered, and it is the reference implementation for this seam.

Two Samsung-shaped assumptions live in shared code:

1. **Platform selection.** `AddDeviceScreen._save()` sets a new device's platform via `_default_platform()` → `registry.platforms()[0]`. With one adapter that is always Samsung, and there is no UI to choose otherwise. A second adapter would be registered but unreachable — no device could ever carry its platform id.
2. **Probe.** `probe_device()` targets the Samsung Tizen info endpoint (`http://<ip>:8001/api/v2/`) and its JSON shape. LG has no such endpoint.

This change adds the LG WebOS adapter and the minimum UI needed to make it reachable.

## Goals / Non-Goals

**Goals:**
- Implement the LG WebOS platform against the existing `Adapter`/`Session` seam, mirroring the Samsung adapter's structure and testing approach (injected transport factory, fake in tests, no real TV).
- Let the user choose the target platform when adding a device, so LG devices can be created.
- Keep the single-platform experience unchanged for users who never add a second adapter.

**Non-Goals:**
- No changes to the generic key vocabulary, `Capabilities`, `Session` seam, registry, or device store/model.
- No LG-specific probe/auto-fill — LG falls back to manual entry (probe failure already never blocks).
- No network discovery/SSDP, no app-launch or media-transport features beyond the generic key set.

## Decisions

### Decision: Use `aiowebostv` as the LG WebOS client
The Samsung adapter wraps an async client (`samsungtvws.async_remote`). `aiowebostv` is the async WebOS/SSAP client used by Home Assistant's `webostv` integration — actively maintained, handles the client-key handshake and the SSAP request/subscription model, and matches the async style already in the codebase.

**Alternatives considered:**
- `bscpylgtv` — capable and async, but less widely deployed than the HA-backed library.
- `pywebostv` — synchronous; would force thread-offloading to fit the async adapter and session, adding complexity.

### Decision: Map generic keys onto SSAP + the input channel
LG WebOS splits control across two mechanisms. Volume, mute, and power are SSAP service requests (`ssap://audio/volumeUp`, `ssap://audio/volumeDown`, `ssap://audio/setMute`, `ssap://system/turnOff`). Directional/OK/BACK/HOME are button events sent over the input (pointer/remote) channel (`UP`, `DOWN`, `LEFT`, `RIGHT`, `ENTER`, `BACK`, `HOME`). The adapter hides this split behind a single `LG_KEYS` mapping and a `_dispatch_key` that routes each key to the right mechanism, so callers still speak only generic `Key`s. All 11 generic keys are covered, so LG declares the same capability key set as Samsung.

### Decision: Client-key pairing reuses the credential flow verbatim
LG pairing returns a client-key on first accept, replayed on later connects — structurally identical to Samsung's token. `pair()` returns the client-key string; `connect()` passes the stored `device.credential`. No changes to the pairing lifecycle, the `Prompt` hook, or the store.

### Decision: Platform selector in `AddDeviceScreen`, hidden for a single adapter
Add a `Select` populated from `registry.platforms()`, defaulting to the first, and store the chosen value on the `Device`. When `len(platforms) <= 1` the selector is not shown and the sole platform is assigned automatically — preserving today's Samsung-only UX and honoring "nothing else new" for existing users. Editing a device does not change its platform (the field is set once, at add time).

**Alternatives considered:**
- Always show the selector — adds a redundant control for single-adapter users.
- A separate platform-picker screen before the form — heavier than warranted for one dropdown.

### Decision: Text via `insertText`, still best-effort
LG exposes text entry via `ssap://com.webos.service.ime/insertText`. It is generally more reliable than Samsung's, but the adapter still declares `text=True` and raises `TextUnsupportedError` on failure so the session reports it rather than silently dropping input — matching the seam's contract.

## Risks / Trade-offs

- **`aiowebostv` API surface differs from `samsungtvws`.** → Isolate all library calls inside `adapters/lg.py` behind an injected factory; tests use a fake, so the seam and UI never depend on the library shape.
- **LG probe unsupported → no auto-fill.** → Accepted; manual entry already works and probe failure never blocks adding. Documented in the proposal.
- **Power-on depends on the TV's Wake-on-LAN setting** (as with Samsung). → Same best-effort contract and MAC requirement; no new behavior to explain.
- **Selecting the wrong platform for a device yields connect failures.** → Default to the first platform and keep the list short; a mis-set platform is correctable by deleting and re-adding.

## Open Questions

- Exact `aiowebostv` entry points for the input-channel button send vs SSAP request — to be confirmed against the installed version during implementation.
- Whether pairing surfaces a cancellable prompt distinct from the connect timeout, or relies on the accept-timeout like Samsung — confirm during implementation to satisfy the "pairing can be cancelled" core requirement.
