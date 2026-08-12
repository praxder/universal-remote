## Why

The remote ships two adapters (Samsung Tizen, LG WebOS) behind a brand-agnostic seam built so a new platform is "one new adapter module + register it." Apple TV is the next most common living-room platform. Adding it exercises two parts of the seam that Samsung and LG never touched:

- **PIN pairing.** The `Adapter.pair()` hook already accepts a `Prompt` callback whose comment reads *"a future PIN-based adapter uses it."* Apple TV is that adapter: it displays a PIN the user must type back into the app. No existing adapter uses the hook, and `PairingScreen` never passes one — so the flow works end-to-end today only for popup-style pairing.
- **Connection identity.** `pyatv.connect()` needs a device identity and a service, not just an IP; and its credentials are per-protocol. The `Device` model has no identifier slot.

This change adds the Apple TV adapter and the minimum UI and model changes needed to make it reachable and pairable.

## What Changes

- Add an **Apple TV adapter** implementing the existing `Adapter` seam over the **Companion** protocol via `pyatv`: capability declaration, PIN pairing, connect/session, and key mapping. Registered under a stable `apple-tv` platform identifier.
- Wire **PIN entry into `PairingScreen`**: the screen supplies a `prompt` callback to `adapter.pair(...)`; when the adapter requests a value, the screen presents a PIN-entry state, and the entered value is returned to the adapter. Adapters that never call the prompt (Samsung, LG) keep their current guidance-only flow unchanged. Pairing guidance becomes adapter-driven rather than hardcoded to "Accept the authorization popup on your TV."
- Add a reconnection **`identifier` field** to the `Device` model and persist it alongside the credential. Apple TV needs the device's `pyatv` identifier to verify it is still the device at a given IP before connecting; other platforms leave it unset.
- Add the `pyatv` dependency.

No changes to the generic key vocabulary, the `Capabilities` model, the `Session` seam, the registry, or the Samsung/LG adapters. MUTE is not offered on Apple TV (no Companion equivalent); the existing capability-driven button gating disables it with no UI change.

## Capabilities

### New Capabilities
- `apple-tv-adapter`: An adapter for the Apple TV platform — registration, declared capabilities, Companion PIN pairing, key mapping over `pyatv`'s remote control, best-effort text entry, and connect via a fast host scope-scan that verifies device identity.

### Modified Capabilities
- `device-management`: The persistent device store gains an optional adapter-specific **reconnection identifier**, round-tripped alongside the credential so an adapter can re-establish a connection.
- `tui-remote`: The Use-Remote pairing flow gains **PIN entry** — the pairing screen prompts for and returns a value when the adapter requests one, and its guidance is adapter-driven.

## Impact

- **New code**: `src/universal_remote/adapters/appletv.py` (adapter + session + `register`).
- **Modified code**: `cli.py` (register Apple TV); `tui/remote_flow.py` (PIN-entry state in `PairingScreen`, pass `prompt` to `pair()`); `devices/models.py` (`identifier` field).
- **Dependencies**: adds `pyatv` to `pyproject.toml`.
- **Unchanged**: `keys.py`, `capabilities.py`, `session.py`, `registry.py`, `adapter.py`, the device store's file format contract (an added optional field, tolerated by existing load), and the Samsung and LG adapters.
