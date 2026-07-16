## Context

Adding a device is a manual, IP-first form (`AddDeviceScreen`): the user picks a platform, types a name and an IP, and saves. Pairing is deferred — `store.add(Device(name, platform, ip))` writes only identity and reachability; the credential is obtained later in the Use-Remote flow.

Every supported platform announces itself on the LAN:

| Platform | Mechanism | Tooling | Yields |
|---|---|---|---|
| Apple TV | mDNS | `pyatv.scan()` (built-in) | name, ip, identifier |
| Android TV | mDNS `_androidtvremote2._tcp` | `zeroconf` (present via pyatv) | name, ip |
| Fire TV | mDNS `_amzn-wplay._tcp` | `zeroconf` | name, ip |
| Roku | SSDP `roku:ecp` → ECP `/query/device-info` | none in tree | name, ip |
| Samsung | SSDP `urn:samsung.com:...` → UPnP XML | none in tree | name, ip |
| LG webOS | SSDP `urn:lge-com:...` → UPnP XML | none in tree | name, ip |

The codebase already separates transport from brand knowledge: `reachability.py` is a standalone, app-free TCP probe, and each adapter declares its own `reachability_port` (read via `getattr`). Optional adapter capabilities live *outside* the `runtime_checkable` `Adapter` Protocol and are read with `getattr(adapter, "...", default)` (`reachability_port`, `requires_pairing`). Discovery follows this exact grain.

## Goals / Non-Goals

**Goals:**
- Discover devices for every supported platform and present each as name + platform + IP.
- Let the user add a discovered device by selecting it, with manual entry preserved as a fallback.
- Keep discovery best-effort: a platform that cannot be found (off, unsupported, ADB disabled) simply contributes nothing.
- Stream results into the UI as scans answer; never block the user from reaching manual entry.

**Non-Goals:**
- Pairing or connecting during discovery — auto-add writes identity only, exactly like manual add.
- Continuous/background discovery — a scan runs per visit to the discovery screen, then stops.
- Editing a discovered device before saving — select adds it as-is; the user edits afterward via the existing edit flow.
- Reachability bubbles on discovered rows — a discovered device answered by definition.

## Decisions

### 1. `discovery.py` is pure transport; adapters own brand knowledge
A new standalone module (app-free, unit-testable, mirroring `reachability.py`) provides two transport helpers and a result type:
- `DiscoveredDevice(name, platform, ip, identifier=None)`
- `browse_mdns(service_type, timeout)` — one shared `AsyncZeroconf` per run
- `search_ssdp(target, timeout)` — via `async-upnp-client`; returns responders (ip + LOCATION)

Each adapter that can discover gets an optional `async def discover(self, timeout) -> list[DiscoveredDevice]`, read via `hasattr`/`getattr` like `reachability_port`. Name resolution genuinely differs per brand (Roku via ECP, Samsung/LG via UPnP device XML, mDNS via TXT/instance name), so that quirk lives *in* the adapter; `discovery.py` never learns a brand.

*Alternative considered — a shared matcher engine* (discovery.py owns service-type→platform routing and name parsing): rejected. It would pull brand-specific XML/TXT parsing into the transport layer, breaking the separation `reachability.py` established, and pyatv's scan is an opaque black box that cannot be fed raw hits anyway.

### 2. Adapter fan-out, orchestrated by the screen
`DiscoverScreen` calls every `adapter.discover()` concurrently (one Textual worker each, the `run_worker` idiom the reachability picker already uses), and streams each result into the option list as it returns. This mirrors the reachability picker's per-device fan-out rather than a synchronized batch.

### 3. Fixed platform priority resolves multi-protocol collisions
The only realistic collision is mDNS: a Fire TV answers both `_amzn-wplay._tcp` (→ `firetv`) and `_androidtvremote2._tcp` (→ `androidtv`); a plain Android TV never answers the Amazon service. SSDP platforms use vendor-specific search targets, so Roku/Samsung/LG never cross-claim. Merge results, group by IP, and when an IP carries more than one platform keep the highest-priority one. Priority order (highest first): `firetv`, then `androidtv`; all others unique. This lives in the orchestration layer (cross-adapter policy), not any single adapter.

*Alternatives considered:* showing both rows (confusing — one box, two entries) and probing to disambiguate (slower, and the protocol answer set already disambiguates). The priority rule is exact for the one collision that exists.

### 4. Exclude already-saved devices by IP
Before rendering, drop any discovered device whose IP is already in the store — the user is here to add *new* devices. Comparison is exact-trimmed IP (the same basis the store's `find_conflict` uses for IP).

### 5. Auto-add writes identity only; capture the Apple TV identifier
Selecting a discovered device calls `store.add(Device(name, platform, ip, identifier=...))`. Pairing stays in Use-Remote. `AppleTvAdapter.connect` already validates `config.identifier == device.identifier`, so persisting the identifier the scan provides makes the first connect cleaner; other platforms leave it `None`.

### 6. Use `async-upnp-client` for SSDP; do not hand-roll multicast
Roku/Samsung/LG need SSDP and nothing in the tree provides it. Hand-rolled multicast M-SEARCH has real multi-NIC/VPN pitfalls (a socket binds one interface; a laptop on Wi-Fi + VPN can miss the TV's subnet) and response-timing complexity. `async-upnp-client` (the library Home Assistant uses) handles this. `zeroconf` is already present transitively via `pyatv`; promote it to a direct dependency since we import it directly.

## Risks / Trade-offs

- **Coverage is partial in the real world** (Fire TV needs ADB manually enabled; Samsung Tizen discoverability varies by model and standby state). → Accepted by design: manual entry is always the last row, and discovery never errors when a platform is absent.
- **Multiple mDNS instances** (pyatv runs its own; Android/Fire browse) can be wasteful or noisy on some hosts. → `browse_mdns` uses a single shared `AsyncZeroconf` for the app's own browses; pyatv's internal one is separate but short-lived and bounded by the scan timeout.
- **Multicast may be blocked** on some networks (client isolation, VLANs). → Best-effort contract; manual entry remains.
- **A discovered name may collide with a saved name** (distinct device, same friendly name). → Auto-add reuses the store's `find_conflict`; on a name collision the add is reported and skipped rather than silently overwriting (the user can add it manually with a different name). IP collisions cannot occur because saved IPs are already excluded from the list.
- **New dependency surface** (`async-upnp-client`). → Scoped to SSDP discovery; isolated behind `discovery.py`.

## Open Questions

None blocking. Deferred: whether Samsung's mDNS service (`_samsungmsf._tcp`) is a more reliable path than SSDP for some models — revisit only if SSDP coverage proves poor in practice.
