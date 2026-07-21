## Why

Samsung Tizen is the only supported platform that auto-discovery never finds. Every other platform appears; Samsung never does. The Samsung adapter searches for the device type `urn:samsung.com:device:RemoteControlReceiver:1` via a directed SSDP M-SEARCH, but that is the *legacy* Samsung remote generation. The modern Tizen 2016+ TVs this adapter actually drives (over the `samsungtvws` WebSocket on port 8002) do not reliably answer that directed M-SEARCH, so the scan returns nothing.

The fix is proven reachable by our own code: the Apple TV adapter's `pyatv` scan already sees Samsung TVs over mDNS `_airplay._tcp` and deliberately discards them (`adapters/appletv.py:99`). The device is on the wire and announcing itself — the Samsung adapter is simply looking through the wrong protocol.

## What Changes

- Switch `SamsungTizenAdapter.discover()` from SSDP (`search_ssdp` + `resolve_upnp_name`) to an mDNS `_airplay._tcp.local.` browse via the existing `browse_mdns` seam, mirroring the pattern already used by the Android TV and Fire TV adapters.
- Filter mDNS hits to Samsung by the AirPlay TXT `manufacturer` key (case-insensitive `samsung` prefix), so the Samsung adapter reports only Samsung TVs and never claims an Apple TV or LG that also answers `_airplay._tcp`.
- Remove the now-unused SSDP discovery wiring from the Samsung adapter: `DISCOVERY_TARGET`, the `search`/`resolve_name` constructor seams, and the `SsdpHit`/`resolve_upnp_name`/`search_ssdp` imports. Add an mDNS browse seam (`browse`) instead.
- No change to pairing or control: `pair()` and `connect()` still use `samsungtvws` on port 8002; only how the IP is *found* changes.

## Capabilities

### New Capabilities
<!-- none -->

### Modified Capabilities
- `device-discovery`: The collision/cross-claim requirement's rationale changes. It currently states "the SSDP-based platforms use distinct, vendor-specific discovery targets and do not cross-claim." Samsung now shares the `_airplay._tcp` service with Apple TV (and LG), so the guarantee that keeps Samsung from cross-claiming becomes the adapter's manufacturer-TXT filter rather than a distinct SSDP target. Add a scenario: a non-Samsung AirPlay TV answering the mDNS browse is not reported as Samsung.
- `samsung-tizen-adapter`: Add a network-discovery requirement (the spec currently has none). The adapter SHALL discover Samsung TVs via an mDNS `_airplay._tcp` browse, restricted to responders whose AirPlay metadata identifies the manufacturer as Samsung, reporting each with its friendly name and IP.

## Impact

- **Code**: `src/universal_remote/adapters/samsung.py` (discovery method + imports + constructor seam). No change to `discovery.py` transport (`browse_mdns` already exists). Discovery policy in `discovery.py` (`merge`/priority) is unaffected — Apple TV's Companion filter already prevents an IP collision, and the manufacturer filter keeps the Samsung adapter Samsung-only.
- **Tests**: `tests/test_samsung_adapter.py` discovery tests move from SSDP fakes (`SsdpHit`/`resolve_name`) to mDNS fakes (`MdnsHit`/`browse`), including a non-Samsung hit that must be filtered out.
- **Dependencies**: None added. `zeroconf` (via `browse_mdns`) is already a dependency; the `samsungtvws`, `async_upnp_client` deps are unchanged (SSDP UPnP name resolution is no longer used by Samsung but may still be used by LG).
- **Behavior/risk**: The exact AirPlay TXT key/value for Samsung manufacturer must be confirmed on real hardware (HA's manifest uses `manufacturer` starting with `samsung`); a wrong key is a one-line fix. Legacy pre-2016 Samsung sets that only answered the old SSDP target will no longer be discovered (they were never controllable by this `samsungtvws`-based adapter anyway).
