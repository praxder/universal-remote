## 1. Confirm the discovery signal

- [ ] 1.1 Confirm the AirPlay TXT key/value a real Samsung Tizen TV publishes for manufacturer (assume key `manufacturer`, value beginning `Samsung`); note the actual key/value so the filter matches. If manufacturer is absent, record which TXT key identifies Samsung.

## 2. Tests first (red)

- [ ] 2.1 Rewrite the Samsung discovery tests in `tests/test_samsung_adapter.py` to inject an mDNS `browse` seam returning `MdnsHit`s instead of the SSDP `search`/`resolve_name` seams.
- [ ] 2.2 Add a test: a Samsung `MdnsHit` (manufacturer TXT = Samsung) is reported under the `samsung-tizen` platform with its instance name and IP.
- [ ] 2.3 Add a test: a non-Samsung `_airplay._tcp` hit (e.g. manufacturer `Apple`/`LGE`, or missing manufacturer) is filtered out and not reported.
- [ ] 2.4 Add a test: a Samsung hit with a blank instance name falls back to its IP (via `DiscoveredDevice`).
- [ ] 2.5 Run the file and confirm the new discovery tests fail for the right reason.

## 3. Implementation (green)

- [ ] 3.1 In `adapters/samsung.py`, replace the SSDP discovery imports/constants: drop `SsdpHit`, `resolve_upnp_name`, `search_ssdp`, and `DISCOVERY_TARGET`; import `MdnsHit` and `browse_mdns`; add a `DISCOVERY_SERVICE = "_airplay._tcp.local."` constant.
- [ ] 3.2 Replace the `search`/`resolve_name` constructor seams with a `browse: MdnsBrowser = browse_mdns` seam, mirroring `AndroidTvAdapter`/`FireTvAdapter`.
- [ ] 3.3 Rewrite `discover()` to browse `DISCOVERY_SERVICE`, keep only hits whose manufacturer TXT identifies Samsung (case-insensitive `samsung` prefix), and map each kept hit to a `DiscoveredDevice(name=hit.name, platform=PLATFORM, ip=hit.ip)`.
- [ ] 3.4 Run `tests/test_samsung_adapter.py` and confirm all tests pass.

## 4. Spec + docs sync

- [ ] 4.1 Confirm the `device-discovery` and `samsung-tizen-adapter` deltas in this change still match the implemented behavior; adjust if the confirmed TXT key differs from the assumption.
- [ ] 4.2 Update any code comments in `adapters/samsung.py` that still describe SSDP-based discovery.

## 5. Preflight

- [ ] 5.1 Format and lint the changed files.
- [ ] 5.2 Run the full test suite and confirm green.
- [ ] 5.3 (If a Samsung TV is available) verify end-to-end that discovery lists the real TV.
