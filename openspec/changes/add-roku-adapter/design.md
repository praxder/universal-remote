## Context

The remote is built on a brand-agnostic seam: a generic `Key` vocabulary, a `Capabilities` declaration, an `Adapter` protocol (`platform`, `display_name`, `capabilities()`, `pair()`, `connect()`), a `BaseSession` that gates sends against declared capabilities, and an `AdapterRegistry` that maps a device's `platform` string to an adapter. Samsung, LG, and Apple TV are the three reference adapters. Each returns a single opaque credential from `pair()` that later connections replay: Samsung/LG via a TV popup, Apple TV via a PIN typed back through the `Prompt` hook.

Roku breaks that mould in one way no adapter has exercised:

- **Roku's control protocol requires no pairing and issues no credential.** ECP is a plain, unauthenticated HTTP API on `http://<ip>:8060` — `POST /keypress/<Key>` presses a button; `POST /keypress/Lit_<url-encoded-char>` types a character. Any device on the LAN can drive it. There is nothing to pair and nothing to persist. But `UseRemoteScreen.on_option_list_option_selected` routes every device whose `credential is None` into `PairingScreen`, which hardcodes "Accept the authorization popup on your TV." A Roku shows no popup, so that guidance is actively wrong.

## Goals / Non-Goals

**Goals:**
- Implement the Roku platform against the existing `Adapter`/`Session` seam, mirroring the Samsung/LG/Apple TV structure and testing approach (injected transport, in-memory fake, no real hardware).
- Let a no-pairing adapter connect directly, without changing the pairing flow for Samsung, LG, or Apple TV.

**Non-Goals:**
- No pairing, no credential, and no `Device` model change (Roku persists neither a credential nor an identifier).
- No changes to the generic key vocabulary, `Capabilities`, `Session` seam, registry, or the device store's file format.
- No device discovery, info-probe prefill (Roku uses manual IP entry like LG/Apple TV), app-launch, now-playing, or media-transport features beyond the generic key set.
- No PLAY/PAUSE/STOP as discrete keys (ECP exposes only a single Play/Pause toggle), no number pad (Roku remotes have none), and no MENU (no ECP equivalent).

## Decisions

### Decision: Use `rokuecp` over ECP
`rokuecp` (ctalkington) is the async Python ECP client behind Home Assistant's Roku integration — `aiohttp`-based, matching the async, library-wrapping shape of the three existing adapters. It provides the ECP transport (button press, literal text), device-info retrieval for a reachability check, and typed errors. ECP itself is thin enough that raw `aiohttp` would work, but wrapping a maintained library keeps parity with Samsung/LG/Apple TV and avoids re-encoding the `Lit_` escaping and error handling by hand. The adapter owns the `aiohttp.ClientSession` it creates and closes it when the session is released.

### Decision: A no-pairing adapter connects directly via `requires_pairing`
Roku has no pairing step, so the adapter declares `requires_pairing = False`. `UseRemoteScreen` reads it defensively — `getattr(adapter, "requires_pairing", True)` — and routes a credential-less device straight to `ConnectingModal` when the adapter needs no pairing, otherwise to `PairingScreen` as today.

This keeps the change minimal and honest:
- The three existing adapters set nothing; the `getattr` default of `True` preserves their behaviour exactly, so none of them is edited.
- Roku never enters `PairingScreen`, so the misleading popup guidance never renders for it.
- `adapter.py` gains a comment documenting the optional `requires_pairing` convention (mirroring the existing `Prompt` comment) so the seam is self-describing without forcing every adapter to declare the attribute.

The alternative — Roku's `pair()` returns a sentinel credential so the credential-less branch is skipped on the *second* visit — was rejected: the first Use-Remote still mounts `PairingScreen` and paints a frame of wrong guidance, and it overloads `credential` with a fake value. This maintainer already chose to add a dedicated field (`identifier`) rather than overload `credential` for Apple TV; the flag follows that same preference for honest seams.

### Decision: Roku `pair()` is a defensive stub
`Adapter` requires a `pair()` method, but `requires_pairing = False` means the UI never calls Roku's. To satisfy the protocol and fail loudly if it is ever reached, Roku's `pair()` raises `PairingCancelledError` with a note that Roku needs no pairing, rather than returning a fake credential.

### Decision: Capability set — MUTE and channel in, discrete transport/number pad/menu out
Roku (a Roku *TV*, with a tuner) declares support for the directional keys, OK (Select), BACK, HOME, volume up/down, **MUTE** (ECP `VolumeMute`), channel up/down (ECP `ChannelUp`/`ChannelDown`), the combined **PLAY_PAUSE** (ECP `Play` is a single toggle), and rewind/fast-forward (ECP `Rev`/`Fwd`). It does **not** declare discrete PLAY/PAUSE/STOP (no distinct ECP keys), the number pad (Roku remotes have none), or MENU (no ECP equivalent). The on-screen remote already disables any key the active adapter does not declare, so those buttons render disabled with no UI change. Text is declared `text=True` and attempted best-effort via `rokuecp`'s literal entry, reporting `TextUnsupportedError` on failure rather than silently dropping input — matching the seam's contract.

### Decision: Connect verifies reachability; no identity check
ECP is stateless HTTP to a known IP, so `connect()` constructs the `rokuecp` client for `device.ip` and issues a device-info request to confirm the Roku is reachable, raising `ConnectionFailedError` on any failure (unreachable, refused, timeout) — matching Samsung/LG. Unlike Apple TV there is no identifier to verify: ECP carries no device identity the seam persists, and the user supplied the IP directly.

## Risks / Trade-offs

- **`rokuecp` method and key-name vocabulary are unverified from planning.** → Confirm the entry points against the pinned version in task 1.2 (mirroring how the LG change confirmed `aiowebostv` and the Apple TV change confirmed `pyatv`): the client constructor and session injection, the button-press method, the literal-text method, the device-info/update method, the exact ECP key strings, and the error types. Every `rokuecp` call is isolated inside `adapters/roku.py` behind an injected factory; tests use a fake, so the seam and TUI never depend on the library shape.
- **`UseRemoteScreen` gains a branch.** → The branch is a single `getattr` guard reusing the existing direct-connect path; non-Roku adapters take the unchanged pairing branch, and existing pairing tests stay green.
- **Best-effort correctness is only hardware-verifiable.** → As with the other adapters, tests prove the adapter emits the intended `rokuecp` call, not that a real Roku accepts it. Key-name correctness and text support are accepted best-effort, in the same register as the README's existing caveats.

## Open Questions (resolve during implementation)

- **Exact `rokuecp` entry points for the installed version**: the `Roku` client constructor and how the `aiohttp` session is supplied, the button-press method and its accepted key vocabulary, the literal-text method, and the reachability/device-info method plus its error types. Confirm against the pinned version before finalising the key map (task 1.2).
- **MENU mapping**: left unmapped by default (no ECP equivalent); optionally map to `Info` (the `*` key) if that proves useful on hardware. A single dict entry either way.

## Verification Limits

Tests use an in-memory fake `rokuecp` double, so they prove the adapter *emits the ECP action it was handed* and *checks reachability on connect*, not that a real Roku accepts it. Two things are only verifiable on hardware and accepted as best-effort:

- **Key-name correctness** — the mapped ECP strings (`Select` for OK, `Rev`/`Fwd` for rewind/fast-forward, …) must match Roku's vocabulary; a wrong string passes every test and fails silently on the device.
- **Text entry** — literal entry depends on a focused on-screen keyboard; declared `text=True` but reported unsupported on failure.
