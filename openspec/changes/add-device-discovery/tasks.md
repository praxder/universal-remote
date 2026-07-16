## 1. Dependencies

- [ ] 1.1 Add `async-upnp-client` to `pyproject.toml` dependencies and promote `zeroconf` to a direct dependency (currently transitive via `pyatv`); sync the venv/lockfile and confirm imports resolve.

## 2. Discovery transport and policy module (`discovery.py`)

- [ ] 2.1 Write tests for `DiscoveredDevice` and the pure merge/dedup/exclude logic: fixed platform priority (Fire TV over Android TV) collapses one IP to one entry, distinct IPs both survive, saved IPs are excluded by trimmed exact match, and a missing name falls back to the IP.
- [ ] 2.2 Implement `DiscoveredDevice` and the pure `merge`/dedup + `exclude_saved` + name-fallback helpers to pass 2.1 (app-free, no I/O — mirrors `reachability.py`).
- [ ] 2.3 Write tests for `browse_mdns(service_type, timeout)` with an injected fake zeroconf: returns hits within the bounded window, one shared `AsyncZeroconf` per run, and yields nothing (no raise) on failure/timeout.
- [ ] 2.4 Implement `browse_mdns`.
- [ ] 2.5 Write tests for `search_ssdp(target, timeout)` with an injected fake `async-upnp-client` search: returns responders (ip + LOCATION) for a vendor target, bounded window, and yields nothing (no raise) on failure/timeout.
- [ ] 2.6 Implement `search_ssdp`.
- [ ] 2.7 Write tests for `discover(adapters, saved_ips, timeout)`: fans out `adapter.discover()` concurrently over fake adapters, isolates a failing/timing-out adapter (best-effort), then merges + priority-dedups + excludes saved.
- [ ] 2.8 Implement `discover(adapters, saved_ips, timeout)` (takes adapters, not the app, so it stays app-free and testable).

## 3. Per-adapter `discover()`

- [ ] 3.1 Apple TV: test + implement `discover(timeout)` via the injected `pyatv.scan` (network-wide, no `hosts`), mapping name/address/identifier to `DiscoveredDevice(platform="apple-tv", ...)`.
- [ ] 3.2 Android TV: test + implement `discover(timeout)` via `browse_mdns("_androidtvremote2._tcp.local.")` → `platform="androidtv"`.
- [ ] 3.3 Fire TV: test + implement `discover(timeout)` via `browse_mdns("_amzn-wplay._tcp.local.")` → `platform="firetv"`.
- [ ] 3.4 Roku: test + implement `discover(timeout)` via `search_ssdp("roku:ecp")`, resolving the friendly name from ECP `/query/device-info` → `platform="roku"`.
- [ ] 3.5 Samsung: test + implement `discover(timeout)` via `search_ssdp` on the Samsung vendor target, resolving `friendlyName` from the UPnP device description → `platform="samsung"`.
- [ ] 3.6 LG: test + implement `discover(timeout)` via `search_ssdp` on the LG vendor target, resolving `friendlyName` from the UPnP device description → `platform="lg"`.

## 4. TUI discovery screen

- [ ] 4.1 Write TUI tests (Textual pilot, fake adapters + store): discovered rows show name/type/IP and stream in; "+ Add manually" is the always-present last row and is selectable before the scan finishes; selecting it pushes the manual `AddDeviceScreen`; selecting a discovered row calls `store.add` with name/platform/IP (and identifier when present) and returns to the list; Esc dismisses while scanning.
- [ ] 4.2 Implement `DiscoverScreen`: one `run_worker` per `adapter.discover()`, streaming each result into a `DeviceOptionList` (reusing the reachability-picker worker idiom), with the manual row rendered immediately.
- [ ] 4.3 Rewire `DeviceListScreen.action_add` (and the add-entry selection handler) to push `DiscoverScreen`; make `DiscoverScreen`'s manual row push the existing `AddDeviceScreen`.
- [ ] 4.4 Add discovery-screen CSS/banner to `app.py` (title art + a "searching" indicator), consistent with the existing Devices/Add banners.

## 5. Docs and preflight

- [ ] 5.1 Update any in-repo docs/README that describe the add-device flow to mention discovery with manual fallback.
- [ ] 5.2 Preflight: `ruff format` + `ruff check`, run the full test suite (`pytest`), and fix any failures.
