## Why

The remote covers Samsung, LG, Roku, Apple TV, and Fire TV behind a brand-agnostic seam built so a new platform is "one new adapter module + register it." Android TV / Google TV (Sony, TCL, Nvidia Shield, Philips, Chromecast with Google TV) is the last major living-room platform missing.

Its kernel is shared with Fire TV, but its *control layer* is not: Android TV ships the native **Android TV Remote protocol v2** — the same protocol the Google TV phone app uses — enabled by default with **no developer mode**. That is a proper always-on path Fire TV lacks (Fire OS exposes only ADB). So this is a distinct adapter, and its structural twin is **Apple TV**, not Fire TV: a library-backed, PIN-paired, credential-replaying platform. The PIN-entry pairing flow and reconnection plumbing Apple TV added are reused as-is, so this change is small.

## What Changes

- Add an **Android TV adapter** implementing the existing `Adapter` seam over the Android TV Remote v2 protocol via the `androidtvremote2` library: capability declaration, PIN pairing, connect/session, and key mapping. Registered under a stable `androidtv` platform identifier.
- Pairing reuses the **existing PIN-entry flow** in `PairingScreen`: the TV shows a code, `adapter.pair(prompt=…)` requests it through the already-present `prompt` hook, and `PairingScreen` presents its already-built PIN-entry state. No TUI change.
- Add the `androidtvremote2` dependency.

The `androidtvremote2` library reads its client certificate and private key from **files on disk**. `Device.credential` is a single in-memory string and the codebase deliberately keeps pairing keys off disk (Fire TV uses a throwaway temp dir). The adapter therefore bridges the two: pack the paired cert+key into one credential string, and materialize them to an ephemeral temp dir at connect time. See design.md.

No changes to the generic key vocabulary, the `Capabilities` model, the `Session` seam, the registry, the device store's file format, or any existing adapter. Android TV declares the fuller Android key set — including MUTE and channel up/down — which the capability-driven button gating surfaces with no UI change.

## Capabilities

### New Capabilities
- `androidtv-adapter`: An adapter for the Android TV / Google TV platform — registration under `androidtv`, declared capabilities, Android TV Remote v2 PIN pairing yielding a persistable cert+key credential, connect that replays the credential and verifies reachability, generic-key mapping over `send_key_command`, and best-effort text entry.

### Modified Capabilities
<!-- None. PIN-entry pairing (tui-remote) and the reconnection identifier (device-management) already exist from add-appletv-adapter and are reused unchanged. -->

## Impact

- **New code**: `src/universal_remote/adapters/androidtv.py` (adapter + session + `register`).
- **Modified code**: `cli.py` (register Android TV).
- **Dependencies**: adds `androidtvremote2` to `pyproject.toml`.
- **Unchanged**: `keys.py`, `capabilities.py`, `session.py`, `registry.py`, `adapter.py`, `devices/models.py`, the device store's file format, `tui/remote_flow.py` (PIN entry already present), and every existing adapter.
