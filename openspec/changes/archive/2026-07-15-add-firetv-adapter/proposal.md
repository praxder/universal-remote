## Why

The remote ships four adapters (Samsung Tizen, LG WebOS, Apple TV, Roku) behind a brand-agnostic seam built so a new platform is "one new adapter module + register it." Amazon Fire TV is the next most common living-room platform. Unlike Roku and Apple TV, adding it exercises **no** part of the seam that existing adapters have not already covered:

- **Pairing.** Fire OS is an Android fork, and its only viable programmatic control path is **ADB over TCP** (Android TV Remote v2, the PIN-paired Google protocol, is not exposed on Fire OS; there is no companion/DIAL alternative that sends key events). ADB authorization is a **popup on the TV** — identical in shape to Samsung/LG pairing: the user accepts a dialog and the app persists an opaque credential to replay. The one twist is that the credential is a **client-generated RSA private key** rather than a token the TV issues, but it is still a single opaque string stored in `device.credential`.

This change adds the Fire TV adapter alone. It is the purest instance of the seam's design goal: no flow, model, UI, registry, key-vocabulary, or store-format change.

## What Changes

- Add a **Fire TV adapter** implementing the existing `Adapter` seam over **ADB** via `adb-shell`: capability declaration, popup-style pairing that generates and returns an RSA private-key PEM, connect/session, key mapping over ADB key events, and best-effort text entry. Registered under a stable `firetv` platform identifier.
- Add the `adb-shell` dependency.

The adapter uses the **existing** popup-pairing path unchanged: `requires_pairing` defaults to `True`, `pair()` never calls the `prompt` hook (like Samsung/LG), and `PairingScreen`'s existing default guidance — "Accept the authorization popup on your TV." — already describes the ADB authorization dialog. Fire TV declares the full generic key set except channel up/down (a Fire TV streamer has no tuner); the existing capability-driven button gating disables those two buttons with no UI change. Adding a Fire TV uses manual IP entry — the Samsung-only info probe is untouched.

## Capabilities

### New Capabilities
- `firetv-adapter`: An adapter for the Amazon Fire TV platform — registration, declared capabilities, popup-style ADB pairing yielding a persisted RSA private-key credential, key mapping over `adb-shell` key events, best-effort text entry, and connect that replays the stored key and verifies reachability.

## Impact

- **New code**: `src/universal_remote/adapters/firetv.py` (adapter + session + `register`).
- **Modified code**: `cli.py` (register Fire TV).
- **Dependencies**: adds `adb-shell` to `pyproject.toml`.
- **Documentation**: `README.md` gains Fire TV in the platform list, the ADB-debugging prerequisite, and which keys are unavailable (channel up/down).
- **Unchanged**: `keys.py`, `capabilities.py`, `session.py`, `registry.py`, `adapter.py`, `devices/models.py`, `tui/remote_flow.py` (pairing flow and guidance), the device store's file format, and the Samsung, LG, Apple TV, and Roku adapters.
