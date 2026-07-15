## Why

The remote ships three adapters (Samsung Tizen, LG WebOS, Apple TV) behind a brand-agnostic seam built so a new platform is "one new adapter module + register it." Roku is the next most common living-room platform. Adding it exercises one part of the seam that no existing adapter touches:

- **No pairing.** Samsung and LG pair via a TV popup; Apple TV pairs via a PIN. All three return an opaque credential that later connections replay. Roku's External Control Protocol (ECP) is an **unauthenticated HTTP API on the LAN** — there is no pairing step and no credential. But `UseRemoteScreen` sends any credential-less device to `PairingScreen`, which would flash misleading "Accept the authorization popup" guidance for a Roku that has no popup.

This change adds the Roku adapter and the minimum flow change needed to let a no-pairing platform connect directly.

## What Changes

- Add a **Roku adapter** implementing the existing `Adapter` seam over **ECP** via `rokuecp`: capability declaration, connect/session, key mapping, and best-effort text entry. Registered under a stable `roku` platform identifier.
- Let an adapter **declare it needs no pairing**: `UseRemoteScreen` skips `PairingScreen` and connects directly when the resolved adapter reports `requires_pairing` as false. Adapters that do not declare it default to requiring pairing, so Samsung, LG, and Apple TV are unchanged. The Roku adapter sets `requires_pairing = False`.
- Add the `rokuecp` dependency.

No changes to the generic key vocabulary, the `Capabilities` model, the `Session` seam, the registry, the `Device` model, the device store's file format, or the Samsung/LG/Apple TV adapters. Roku declares no PLAY/PAUSE/STOP (ECP has only a single Play/Pause toggle), no number pad, and no MENU; the existing capability-driven button gating disables them with no UI change. Adding a Roku uses manual IP entry — the Samsung-only info probe is untouched.

## Capabilities

### New Capabilities
- `roku-adapter`: An adapter for the Roku platform — registration, declared capabilities, direct connect with no pairing, key mapping over `rokuecp`'s ECP remote, best-effort literal text entry, and a reachability check at connect time.

### Modified Capabilities
- `tui-remote`: The Use-Remote flow connects **directly, skipping pairing**, when the chosen device's adapter declares it needs no pairing; the pairing flow is otherwise unchanged.

## Impact

- **New code**: `src/universal_remote/adapters/roku.py` (adapter + session + `register`).
- **Modified code**: `cli.py` (register Roku); `tui/remote_flow.py` (skip pairing when the adapter needs none); `adapter.py` (documenting comment for the optional `requires_pairing` convention, no behavioural change).
- **Dependencies**: adds `rokuecp` to `pyproject.toml`.
- **Unchanged**: `keys.py`, `capabilities.py`, `session.py`, `registry.py`, `devices/models.py`, the device store's file format, and the Samsung, LG, and Apple TV adapters.
