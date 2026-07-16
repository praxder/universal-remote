## Why

Adding a device today means knowing its platform and typing its IP address by hand — a hurdle for anyone who does not know their TV's address. Every platform we support already announces itself on the local network (mDNS or SSDP), so the app can find devices for the user and let them add one by selecting it, while keeping manual entry as a fallback.

## What Changes

- Add automatic network discovery that scans for devices of every supported platform (Apple TV, Android TV, Fire TV, Roku, Samsung, LG) and reports each device's name, platform, and IP address.
- Insert a new discovery screen between the saved-device list and the manual add form: pressing **Add** now opens a list of discovered devices, with **+ Add manually** as the last row.
- Selecting a discovered device saves it immediately (no manual entry); selecting **+ Add manually** opens the existing manual add form unchanged.
- Discovered devices already in the store are excluded from the list.
- When one device answers on two protocols (a Fire TV answers both the Fire TV and Android TV services), a fixed platform priority resolves it to a single entry (Fire TV wins).
- Add the `async-upnp-client` dependency for SSDP discovery (Roku/Samsung/LG); reuse the already-present `zeroconf` for mDNS (Apple TV/Android TV/Fire TV).

## Capabilities

### New Capabilities
- `device-discovery`: Scans the local network across all supported platforms, identifies each device's name/platform/IP, resolves multi-protocol collisions by a fixed platform priority, excludes already-saved devices, and is best-effort (an unsupported or unreachable platform yields no results rather than an error).

### Modified Capabilities
- `tui-remote`: The **Add** entry opens the new discovery screen instead of the manual add form directly; the discovery screen lists discovered devices (name, type, IP), streams rows as scans answer, offers **+ Add manually** as the last row into the existing manual form, adds a device on selection, and is dismissible while scanning.

## Impact

- **Code**: New `discovery.py` transport module (mDNS + SSDP, standalone and app-free like `reachability.py`); an optional `discover()` on each adapter that can discover, read via `hasattr`/`getattr` like `reachability_port`; a new `DiscoverScreen` in the TUI; the device list's Add action rewired to push it.
- **Dependencies**: Add `async-upnp-client`; promote `zeroconf` to a direct dependency (currently transitive via `pyatv`).
- **Behavior**: The manual add form, the saved-device list, and the Use-Remote flow are unchanged. Pairing still happens later in Use-Remote, so auto-add only writes name/platform/IP (plus the Apple TV identifier when the scan provides it).
