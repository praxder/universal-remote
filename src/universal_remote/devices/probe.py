"""Auto-fill device fields by probing a TV's unauthenticated info endpoint."""

from __future__ import annotations

import json
import urllib.request
from dataclasses import dataclass
from typing import Callable

# A transport that returns the raw body for a URL; injectable so tests never hit
# the network.
Fetcher = Callable[[str], bytes]


@dataclass(frozen=True)
class ProbeResult:
    """Fields discovered from a TV's info endpoint, any of which may be missing."""

    name: str | None
    model: str | None
    mac: str | None


def _default_fetch(url: str) -> bytes:
    with urllib.request.urlopen(url, timeout=3) as response:
        return response.read()


def probe_device(ip: str, fetch: Fetcher = _default_fetch) -> ProbeResult | None:
    """Probe `http://<ip>:8001/api/v2/`; return None on any failure so add never blocks."""
    url = f"http://{ip}:8001/api/v2/"
    try:
        data = json.loads(fetch(url))
    except Exception:
        return None
    device = data.get("device", {})
    return ProbeResult(
        name=device.get("name"),
        model=device.get("modelName"),
        mac=device.get("wifiMac"),
    )
