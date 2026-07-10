## Why

The app ships with one adapter (Samsung Tizen) behind a deliberately brand-agnostic seam. LG WebOS is the next most common TV platform, and the adapter architecture was built precisely so a new platform is "one new adapter module + register it." Adding LG proves the seam and makes the existing app and remote usable with LG TVs.

## What Changes

- Add an **LG WebOS adapter** implementing the existing `Adapter` seam: capability declaration, client-key pairing, connect/session, key mapping, best-effort text, and Wake-on-LAN power-on. Registered under a stable `lg-webos` platform identifier.
- Add a **platform selector to the Add-Device flow** so a user can choose which platform a new device targets. This is required because the current flow hardcodes the first-registered platform (Samsung); without a picker the LG adapter is registered but unreachable. When only one adapter is registered, the picker is hidden so the existing single-platform experience is unchanged.
- Add the LG WebOS client library dependency (`aiowebostv`).

No changes to the generic key vocabulary, capabilities model, session seam, registry, or device store. Probe stays Samsung-specific; LG devices fall back to manual entry (adding is never blocked).

## Capabilities

### New Capabilities
- `lg-webos-adapter`: An adapter for the LG WebOS platform — registration, declared capabilities, client-key pairing, key mapping over the SSAP/input protocol, best-effort text entry, and best-effort Wake-on-LAN power-on.

### Modified Capabilities
- `device-management`: The "Add device" requirement gains platform selection — the user chooses the target platform from the registered adapters (defaulting to the first), and that platform is stored on the device.

## Impact

- **New code**: `src/universal_remote/adapters/lg.py` (adapter + `register`).
- **Modified code**: `cli.py` (register LG adapter); `tui/devices_screen.py` (platform selector in `AddDeviceScreen`).
- **Dependencies**: adds `aiowebostv` to `pyproject.toml`.
- **Unchanged**: `keys.py`, `capabilities.py`, `session.py`, `registry.py`, `adapter.py`, device store/model, and the Samsung adapter.
