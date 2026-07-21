## Context

Auto-discovery fans out one `discover()` per adapter (`discovery.py:discover`) and merges results by IP. Every platform works except Samsung Tizen.

The Samsung adapter (`adapters/samsung.py`) discovers via a directed SSDP M-SEARCH for `urn:samsung.com:device:RemoteControlReceiver:1`, then reads the UPnP `friendlyName`. That target is the *legacy* Samsung remote generation (old port-55000 protocol, UPnP description at `:7676/rcr/`). The modern Tizen 2016+ TVs this adapter controls — over the `samsungtvws` WebSocket on port 8002 — do not reliably answer that directed M-SEARCH, so the scan returns nothing. The SSDP transport itself is sound: Roku and LG use the identical `search_ssdp` path and discover fine, differing only in target string.

Two facts fix the approach:
1. Our own Apple TV adapter already sees Samsung TVs. Its `pyatv` scan over `_airplay._tcp` mDNS is promiscuous — LG and Samsung answer it too — and it explicitly discards non-Companion devices (`adapters/appletv.py:96-113`). The Samsung TV is provably on the wire.
2. `samsungtvws` ships no discovery helper — it is purely a control library — so there is no vendor scan to defer to. Discovery must come from mDNS or SSDP.

`browse_mdns` already exists in `discovery.py` and is the seam the Android TV and Fire TV adapters use. Fire TV even demonstrates reading a friendly name out of a TXT key and filtering on TXT content.

## Goals / Non-Goals

**Goals:**
- Samsung Tizen TVs appear in auto-discovery alongside the other platforms.
- Reuse the established mDNS pattern (`browse_mdns` seam, `MdnsHit`) rather than inventing a new transport.
- Keep the Samsung adapter from claiming Apple TVs or LG TVs that also answer `_airplay._tcp`.
- Leave pairing/control (`samsungtvws`, port 8002) untouched.

**Non-Goals:**
- Discovering legacy pre-2016 Samsung sets (the old SSDP target's generation). This adapter cannot control them regardless.
- Changing the discovery fan-out, merge policy, or priority ranking in `discovery.py`.
- Adding passive SSDP NOTIFY listening or a broad `ssdp:all` search (heavier alternatives, see Decisions).

## Decisions

### Decision: Discover Samsung via mDNS `_airplay._tcp`, not SSDP

Browse `_airplay._tcp.local.` with `browse_mdns` and keep only Samsung responders.

- **Why over the current directed SSDP target**: modern Tizen does not reliably answer `RemoteControlReceiver:1`; `_airplay._tcp` is the path our code already proves Samsung answers.
- **Why over a broad `ssdp:all` search + filter**: `ssdp:all` is noisier and still depends on the TV's SSDP responsiveness, which is the thing that failed. mDNS is the demonstrated-working channel.
- **Why over passive SSDP NOTIFY listening** (how Home Assistant finds Samsung): it needs a long-lived listener, which does not fit the bounded, on-demand `discover(timeout)` model every other adapter uses.
- **Why not the `samsungtvws` REST device-info endpoint** (`http://{ip}:8001/api/v2/`): that needs an IP first; it is a name/detail resolver, not a scanner.

### Decision: Filter to Samsung by the AirPlay `manufacturer` TXT key

`_airplay._tcp` is answered by Apple TVs, LG, and Samsung. Keep a hit only when its TXT metadata identifies the manufacturer as Samsung (case-insensitive `samsung` prefix), matching how Home Assistant's `samsungtv` manifest scopes its `_airplay._tcp` zeroconf entry (`manufacturer: samsung*`).

- Without this filter the Samsung adapter would report every AirPlay TV as `samsung-tizen`.
- This filter is the new cross-claim guard. Previously the "distinct vendor SSDP target" gave that guarantee for free; under shared-service mDNS the adapter must enforce it.

### Decision: No change to collision/merge policy

`discovery.py`'s `merge()` collapses a shared IP to the highest-priority platform. A Samsung TV will surface only from the Samsung adapter:
- Apple TV's adapter already filters to Companion-only, so it will not also report the Samsung IP.
- LG discovers via its own SSDP target; the Samsung manufacturer filter excludes LG.

So no Samsung-vs-Apple priority rule is needed, and `_PLATFORM_PRIORITY` stays `("firetv", "androidtv")`.

### Decision: Friendly name from the mDNS instance name

Like Android TV, use the `MdnsHit.name` (the instance label the TV publishes), falling back to IP inside `DiscoveredDevice` when blank. Drop the SSDP UPnP `resolve_upnp_name` name step entirely for Samsung.

## Risks / Trade-offs

- **The exact AirPlay TXT key/value on real Samsung hardware is unverified** → HA uses `manufacturer` with a `samsung` prefix; confirm on a real TV during implementation. A wrong key or value is a single-line fix, and the change is behind the injectable `browse` seam so it is unit-testable without hardware.
- **A Samsung TV with AirPlay disabled would not advertise `_airplay._tcp`** → it then falls back to manual add (unchanged from today, where it is not discovered at all). No regression.
- **Legacy pre-2016 Samsung sets lose SSDP discovery** → acceptable; the `samsungtvws` adapter never controlled them.
- **If a future Samsung model omits `manufacturer` from its AirPlay TXT** → it would be filtered out. Mitigation: allow an alternate identifying key (e.g. `model`) if hardware testing shows `manufacturer` is absent; capture as a follow-up rather than speculatively widening the filter now (YAGNI).

## Open Questions

- Exact AirPlay TXT key(s) and value casing Samsung Tizen publishes for manufacturer/model — to confirm on real hardware. Default assumption: key `manufacturer`, value beginning `Samsung`.
