"""Local-network device discovery: mDNS + SSDP transport, plus cross-adapter policy.

Standalone by design — no imports from `adapters` or `tui` — so it stays unit-
testable without a running app and free of platform concerns, mirroring
`reachability.py`. Transport helpers browse (mDNS) and search (SSDP) the LAN and
return raw hits; adapters own the brand-specific name resolution. A pure policy
layer resolves multi-protocol collisions by a fixed platform priority and drops
already-saved devices.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable

from async_upnp_client.aiohttp import AiohttpRequester
from async_upnp_client.client_factory import UpnpFactory
from async_upnp_client.search import async_search
from zeroconf import ServiceStateChange
from zeroconf.asyncio import AsyncServiceBrowser, AsyncServiceInfo, AsyncZeroconf


@dataclass
class DiscoveredDevice:
    """A device found on the network: identity plus the platform that found it."""

    name: str
    platform: str
    ip: str
    identifier: str | None = None

    def __post_init__(self) -> None:
        # A device that announces no usable friendly name is shown by its IP.
        self.name = (self.name or "").strip() or self.ip


# Highest priority first. The only real multi-protocol collision is mDNS: a Fire
# TV answers both the Amazon and Android TV services, so it must outrank a plain
# Android TV. Every other platform uses a vendor-specific target and never cross-
# claims, so they share the lowest rank without colliding in practice.
_PLATFORM_PRIORITY = ("firetv", "androidtv")


def _rank(platform: str) -> int:
    if platform in _PLATFORM_PRIORITY:
        return _PLATFORM_PRIORITY.index(platform)
    return len(_PLATFORM_PRIORITY)


def merge(devices: list[DiscoveredDevice]) -> list[DiscoveredDevice]:
    """Collapse devices sharing an IP to the highest-priority platform.

    Order-preserving by first appearance of each IP; distinct IPs all survive.
    """
    by_ip: dict[str, DiscoveredDevice] = {}
    for device in devices:
        ip = device.ip.strip()
        current = by_ip.get(ip)
        if current is None or _rank(device.platform) < _rank(current.platform):
            by_ip[ip] = device
    return list(by_ip.values())


def exclude_saved(
    devices: list[DiscoveredDevice], saved_ips: list[str]
) -> list[DiscoveredDevice]:
    """Drop any device whose IP already belongs to a saved device (trimmed match)."""
    saved = {ip.strip() for ip in saved_ips}
    return [device for device in devices if device.ip.strip() not in saved]


@dataclass
class MdnsHit:
    """A raw mDNS responder: the instance name, its IP, and its decoded TXT record.

    Platform-agnostic on purpose — an adapter turns a hit into a `DiscoveredDevice`,
    choosing the friendly name from the instance name or a brand-specific TXT key.
    """

    name: str
    ip: str
    properties: dict[str, str] = field(default_factory=dict)


# `resolve(azc, service_type, timeout)` — the browse-and-resolve step, injected in
# tests so the transport is unit-testable without a live network.
MdnsResolver = Callable[[AsyncZeroconf, str, float], Awaitable[list[Any]]]


def _hit_from_info(service_type: str, info: Any) -> MdnsHit:
    """Map one resolved service info to a hit, stripping the service-type suffix."""
    addresses = info.parsed_addresses()
    name = info.name
    if name.endswith(service_type):
        name = name[: -len(service_type)]
    return MdnsHit(
        name=name.rstrip("."),
        ip=addresses[0] if addresses else "",
        properties=dict(info.decoded_properties or {}),
    )


async def _resolve_services(
    azc: AsyncZeroconf, service_type: str, timeout: float
) -> list[AsyncServiceInfo]:
    """Browse for `timeout` seconds on the shared zeroconf, then resolve each hit."""
    names: list[str] = []

    def _on_change(zeroconf, service_type, name, state_change) -> None:
        if state_change is ServiceStateChange.Added:
            names.append(name)

    browser = AsyncServiceBrowser(azc.zeroconf, service_type, handlers=[_on_change])
    try:
        await asyncio.sleep(timeout)
    finally:
        await browser.async_cancel()
    infos: list[AsyncServiceInfo] = []
    for name in names:
        info = AsyncServiceInfo(service_type, name)
        if await info.async_request(azc.zeroconf, int(timeout * 1000)):
            infos.append(info)
    return infos


async def browse_mdns(
    service_type: str,
    timeout: float,
    *,
    zeroconf_factory: Callable[[], AsyncZeroconf] = AsyncZeroconf,
    resolve: MdnsResolver = _resolve_services,
) -> list[MdnsHit]:
    """Discover mDNS responders for `service_type` within a bounded window.

    Uses one shared `AsyncZeroconf` per run. Best-effort: any failure or timeout
    yields no hits rather than raising, and the shared zeroconf is always closed.
    """
    azc = zeroconf_factory()
    try:
        infos = await resolve(azc, service_type, timeout)
    except Exception:
        infos = []
    finally:
        await azc.async_close()
    return [_hit_from_info(service_type, info) for info in infos]


@dataclass
class SsdpHit:
    """A raw SSDP responder: its IP and the LOCATION URL of its UPnP description."""

    ip: str
    location: str


# `search(async_callback, search_target, timeout)` — the SSDP M-SEARCH, injected in
# tests so the transport is unit-testable without a live network.
SsdpSearch = Callable[..., Awaitable[None]]


async def search_ssdp(
    target: str,
    timeout: float,
    *,
    search: SsdpSearch = async_search,
) -> list[SsdpHit]:
    """Search for SSDP responders for `target` within a bounded window.

    Best-effort: hits are collected as they answer, so a mid-search failure keeps
    whatever was already found, and any error yields no raise.
    """
    hits: list[SsdpHit] = []

    async def _collect(headers) -> None:
        remote = headers.get("_remote_addr")
        hits.append(
            SsdpHit(
                ip=remote[0] if remote else "",
                location=headers.get("location") or "",
            )
        )

    try:
        await search(
            async_callback=_collect, search_target=target, timeout=int(timeout)
        )
    except Exception:
        pass
    return hits


async def resolve_upnp_name(location: str) -> str | None:
    """Read a device's friendlyName from its UPnP description at `location`.

    Generic UPnP transport shared by the SSDP adapters (Samsung/LG); the brand
    knowledge (which search target, which platform) stays in each adapter.
    """
    device = await UpnpFactory(AiohttpRequester()).async_create_device(location)
    return device.friendly_name


async def discover_one(adapter: Any, timeout: float) -> list[DiscoveredDevice]:
    """Run one adapter's scan, bounded and isolated — a failure yields no results.

    The adapter self-bounds its scan to `timeout` (an mDNS browse sleeps the whole
    window; `pyatv.scan` runs for it), so the isolation backstop is generously above
    that — it exists to cut a genuinely hung scan, not a scan that used its window.
    """
    try:
        return await asyncio.wait_for(adapter.discover(timeout), timeout * 2)
    except Exception:
        return []


async def discover(
    adapters: list[Any], saved_ips: list[str], timeout: float
) -> list[DiscoveredDevice]:
    """Fan out every adapter's `discover()` concurrently, then apply policy.

    Adapters without a `discover` method contribute nothing. Each scan is bounded
    and isolated so a failing or hanging adapter never aborts the others. Results
    are collision-resolved by platform priority and stripped of already-saved IPs.
    """
    discoverers = [adapter for adapter in adapters if hasattr(adapter, "discover")]
    results = await asyncio.gather(
        *(discover_one(adapter, timeout) for adapter in discoverers)
    )
    found = [device for result in results for device in result]
    return exclude_saved(merge(found), saved_ips)
